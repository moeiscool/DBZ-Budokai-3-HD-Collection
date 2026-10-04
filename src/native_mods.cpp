#include "native_mods.h"

#include "launcher/settings.h"

#include <rex/filesystem.h>
#include <rex/logging.h>

#include <chrono>
#include <ctime>

#include <fstream>
#include <cstring>

namespace dbz3 {
namespace {

constexpr char kSpfMagic[] = "#SPF 1.0";

const std::vector<NativeModInfo> kCatalog = {
    {"save_100", "Guardar al 100%",
     "Instala una partida completa de Xbox 360 (todo desbloqueado). Tu partida se copia antes y se puede restaurar.",
     "Progreso / guardado", NativeModState::kReady},
    {"infinite_health", "Vida infinita",
     "Mantiene la vida del jugador al maximo durante los combates.",
     "Gameplay", NativeModState::kNoKnownPatch},
    {"infinite_ki", "Ki infinito",
     "Evita que el ki del jugador disminuya durante los combates.",
     "Gameplay", NativeModState::kNoKnownPatch},
};

bool IsDataFile(const std::filesystem::path& path) {
  return path.filename() == "data.bin" && std::filesystem::is_regular_file(path);
}

constexpr char kProfile[] = "B13EBABEBABEBABE";
constexpr char kTitle[] = "4E4D0856";

std::filesystem::path TemplateDir() {
  return rex::filesystem::GetExecutableFolder() / "mods_nativos" / "partida_100";
}
std::filesystem::path BackupRoot() { return settings::UserDataRoot() / "respaldos_partida"; }

bool CopyAtomic(const std::filesystem::path& from, const std::filesystem::path& to,
                std::error_code& ec) {
  std::filesystem::create_directories(to.parent_path(), ec);
  if (ec) return false;
  auto tmp = to;
  tmp += ".tmp";
  std::filesystem::copy_file(from, tmp, std::filesystem::copy_options::overwrite_existing, ec);
  if (ec) return false;
  std::filesystem::rename(tmp, to, ec);
  return !ec;
}

}  // namespace

bool Save100Available() {
  return IsSupportedNativeSave(TemplateDir() / "data.bin") &&
         std::filesystem::is_regular_file(TemplateDir() / "DBZ3.header");
}

bool ApplySave100(std::string& message) {
  if (!Save100Available()) {
    message = "Falta la partida al 100% en mods_nativos/partida_100.";
    return false;
  }
  const auto root = settings::UserDataRoot();
  std::error_code ec;
  // 1. Backup of every profile folder (all content, not only data.bin).
  char stamp[32] = {};
  const std::time_t now = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
  std::tm tm{};
  localtime_s(&tm, &now);
  std::strftime(stamp, sizeof(stamp), "%Y%m%d_%H%M%S", &tm);
  const auto dest = BackupRoot() / stamp;
  bool any = false;
  for (const auto& e : std::filesystem::directory_iterator(root, ec)) {
    const auto name = e.path().filename().string();
    if (!e.is_directory() || name.size() != 16) continue;
    std::filesystem::create_directories(dest, ec);
    std::filesystem::copy(e.path(), dest / name, std::filesystem::copy_options::recursive, ec);
    if (ec) {
      message = "No se pudo copiar tu partida; no se ha cambiado nada: " + ec.message();
      return false;
    }
    any = true;
  }
  // 2. Install into each existing profile (or the default one).
  std::vector<std::filesystem::path> profiles;
  for (const auto& e : std::filesystem::directory_iterator(root, ec))
    if (e.is_directory() && e.path().filename().string().size() == 16 &&
        std::filesystem::is_directory(e.path() / kTitle))
      profiles.push_back(e.path());
  if (profiles.empty()) profiles.push_back(root / kProfile);
  for (const auto& p : profiles) {
    if (!CopyAtomic(TemplateDir() / "data.bin", p / kTitle / "00000001" / "DBZ3" / "data.bin", ec) ||
        !CopyAtomic(TemplateDir() / "DBZ3.header", p / kTitle / "Headers" / "00000001" / "DBZ3.header", ec)) {
      message = "Error al instalar la partida: " + ec.message();
      return false;
    }
  }
  message = any ? "Partida al 100% instalada. Copia de tu partida: " + dest.string()
                : "Partida al 100% instalada (no habia partida previa).";
  REXLOG_INFO("dbz3: save_100 applied ({})", message);
  return true;
}

bool RestoreLastSaveBackup(std::string& message) {
  std::error_code ec;
  std::filesystem::path last;
  for (const auto& e : std::filesystem::directory_iterator(BackupRoot(), ec))
    if (e.is_directory() && (last.empty() || e.path().filename() > last.filename())) last = e.path();
  if (last.empty()) {
    message = "No hay ninguna copia de partida que restaurar.";
    return false;
  }
  const auto root = settings::UserDataRoot();
  for (const auto& e : std::filesystem::directory_iterator(last, ec)) {
    std::filesystem::copy(e.path(), root / e.path().filename(),
                          std::filesystem::copy_options::recursive |
                              std::filesystem::copy_options::overwrite_existing, ec);
    if (ec) {
      message = "No se pudo restaurar: " + ec.message();
      return false;
    }
  }
  message = "Partida restaurada desde " + last.string();
  return true;
}

const std::vector<NativeModInfo>& NativeModCatalog() { return kCatalog; }

std::vector<std::filesystem::path> FindNativeSaveFiles() {
  std::vector<std::filesystem::path> result;
  const auto root = settings::UserDataRoot();
  std::error_code ec;
  if (!std::filesystem::is_directory(root, ec)) return result;

  std::filesystem::recursive_directory_iterator it(
      root, std::filesystem::directory_options::skip_permission_denied, ec);
  const std::filesystem::recursive_directory_iterator end;
  for (; it != end; it.increment(ec)) {
    if (ec) {
      ec.clear();
      continue;
    }
    if (!it->is_regular_file(ec) || !IsDataFile(it->path())) continue;
    result.push_back(it->path());
  }
  return result;
}

bool IsSupportedNativeSave(const std::filesystem::path& save) {
  std::ifstream in(save, std::ios::binary);
  if (!in.is_open()) return false;
  char magic[sizeof(kSpfMagic) - 1] = {};
  in.read(magic, sizeof(magic));
  return in.gcount() == static_cast<std::streamsize>(sizeof(magic)) &&
         std::memcmp(magic, kSpfMagic, sizeof(magic)) == 0;
}

bool BackupNativeSave(const std::filesystem::path& save,
                      std::filesystem::path& backup,
                      std::string& error) {
  error.clear();
  if (!std::filesystem::is_regular_file(save)) {
    error = "No se encontro el guardado.";
    return false;
  }
  if (!IsSupportedNativeSave(save)) {
    error = "El guardado no tiene un formato reconocido (#SPF).";
    return false;
  }

  backup = save;
  backup += ".native.bak";
  std::error_code ec;
  std::filesystem::copy_file(save, backup,
                             std::filesystem::copy_options::overwrite_existing, ec);
  if (ec) {
    error = "No se pudo crear la copia de seguridad: " + ec.message();
    return false;
  }
  REXLOG_INFO("dbz3: native save backup created at {}", backup.string());
  return true;
}

}  // namespace dbz3
