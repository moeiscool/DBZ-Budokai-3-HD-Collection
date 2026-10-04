// dbz3 - Select wheel extension (US image): capacity 39 -> 64 cells and NEW cells
// declared by roster mods (roster_ext, `celda = true`).
//
// Wheel data (allocated by sub_8217E6D8, 1448 B; 2368 B here):
//   +0 sprite resource | +12 s8 cells | +16 u64 slot mask | +36 per-player block |
//   +40 current cell | +44 cells x 28 B (+2 s8 slot, +4 icon sprite, +8 frame
//   sprite, +12 ring position) | +1136 ring positions x 8 B (moved to +1840).
// The functions that touch the ring positions are regenerated with the new
// layout by tools/gen_select_wheel.py (select_wheel_gen.inc).
//
// A new cell is a real wheel cell whose slot byte is its HOST slot: the per-slot
// data kept in the save (last costume, 38 records of 4624 B) stays the host's, so
// the save format does not change. While the select logic runs for the player
// standing on a new cell, the slot tables answer with the new character (slot -> ID
// lists, portrait fids, name and icon images) and the host's "Custom" capsule list
// is swapped with the new character's own (roster_ext: mods/capsulas_custom.txt).

#include "roster_ext.h"

#include <rex/hook.h>
#include <rex/logging.h>

#include "generated/dbz3_init.h"

#include <algorithm>
#include <array>
#include <cstdio>
#include <string>
#include <cstring>
#include <mutex>
#include <unordered_map>
#include <vector>

// trazas de diagnostico (roster_trace.cpp, dbz1_diag_logging)
void dbz3_trace_sub_8217F3F0(PPCContext& ctx, uint8_t* base);
void dbz3_trace_sub_8217F520(PPCContext& ctx, uint8_t* base);
void dbz3_trace_sub_82180AA0(PPCContext& ctx, uint8_t* base);

namespace {

using dbz3::roster::GetVirtualCell;
using dbz3::roster::VirtualCellCount;

constexpr uint32_t kCells = 64;
constexpr uint32_t kCellBase = 44;
constexpr uint32_t kCellSize = 28;
constexpr uint32_t kPosBase = 1840;
constexpr uint32_t kRealSlots = 39;   // 38 personajes + aleatorio
constexpr uint32_t kRandomSlot = 38;
constexpr uint32_t kSlotToId[3] = {0x82020618, 0x82021470, 0x82024760};
constexpr uint32_t kPortraits = 0x82372818;

std::mutex g_mu;
// datos de rueda -> casilla nueva de cada celda (-1 = casilla original)
std::unordered_map<uint32_t, std::array<int8_t, kCells>> g_wheels;
// objetos rueda creados por sub_8217E6D8 (+48 = datos de la rueda)
std::unordered_map<uint32_t, uint32_t> g_wheel_objs;
// objeto retrato -> casilla nueva que lo pidio (-1 = ninguna)
std::unordered_map<uint32_t, int> g_portrait_obj;

// Casillas nuevas que aparecen en una rueda: en los modos libres (la rueda tiene la
// casilla aleatoria), siempre disponibles (el slot anfitrion solo aporta los datos
// guardados por slot, aunque no este desbloqueado).
std::vector<int> NewCellsFor(uint64_t mask) {
  std::vector<int> out;
  if (!((mask >> kRandomSlot) & 1)) return out;
  uint32_t n = 0;
  for (uint32_t s = 0; s < kRealSlots; ++s) n += (mask >> s) & 1;
  for (int i = 0; i < VirtualCellCount() && n < kCells; ++i, ++n) out.push_back(i);
  return out;
}

bool GuestPtr(uint32_t p) { return p >= 0x40000000u && p < 0xA0000000u && !(p & 3); }

int NewCellOfWheel(uint8_t* base, uint32_t d) {
  std::lock_guard<std::mutex> lk(g_mu);
  auto it = g_wheels.find(d);
  if (it == g_wheels.end()) return -1;
  const uint32_t cur = REX_LOAD_U32(d + 40);
  if (cur < d + kCellBase) return -1;
  const uint32_t k = (cur - d - kCellBase) / kCellSize;
  return k < kCells ? it->second[k] : -1;
}

// per-player select state (+40 wheel object, whose +48 is the wheel data)
int NewCellOfState(uint8_t* base, uint32_t st) {
  if (!GuestPtr(st)) return -1;
  const uint32_t wobj = REX_LOAD_U32(st + 40);
  {
    std::lock_guard<std::mutex> lk(g_mu);
    if (!g_wheel_objs.count(wobj)) return -1;
  }
  return NewCellOfWheel(base, REX_LOAD_U32(wobj + 48));
}

// ---- imagenes propias (icono de la rueda / rotulo del nombre) ----
// Un descriptor de imagen del recurso de sprites del select (#ACA 2026) acaba en un
// bloque [textura del #AZT 2027, 3, 1.0f, 0, x0, y0, x1, y1] (rect logico) y lleva
// en +0x20 el quad centrado. Se clona una plantilla con otra textura/rect/quad:
// icono = imagen 61 (bloque en +0xB0), rotulo = imagen 105 (+0x60). El sprite del
// rotulo dibuja la textura ENTERA a su tamano logico, asi que cada rotulo nuevo es
// una textura propia anadida al #AZT 2027 por roster_build.py.
struct ImageTemplate {
  uint32_t img;
  uint32_t tex_block;
};
constexpr ImageTemplate kIconTpl{61, 0xB0};
constexpr ImageTemplate kNameTpl{105, 0x60};
constexpr uint32_t kIconImageBase = 61;
constexpr uint32_t kNameImageBase = 105;
constexpr uint32_t kImages = 145;
constexpr uint32_t kSelectGlobal = 0x8245F190;  // +16 = recurso de sprites del select
constexpr uint32_t kSpriteScale = 0x8201F60C;   // float que pasa sub_8217E090

struct BuiltImage {
  uint32_t buf = 0;
  uint32_t cap = 0;
  uint32_t tpl = 0;
};
std::unordered_map<int, BuiltImage> g_images;  // clave: casilla * 2 + (0 icono / 1 rotulo)

uint32_t SpriteTable(uint8_t* base, uint32_t res) {
  return GuestPtr(res) ? REX_LOAD_U32(res + 28) : 0;
}

uint32_t BuildImage(uint8_t* base, uint32_t tbl, int vc, bool name) {
  const int32_t* r = name ? GetVirtualCell(vc).name : GetVirtualCell(vc).icon;
  if (r[0] < 0 || !GuestPtr(tbl)) return 0;
  const ImageTemplate t = name ? kNameTpl : kIconTpl;
  const uint32_t src = REX_LOAD_U32(tbl + 4 * t.img);
  if (!GuestPtr(src) || REX_LOAD_U32(src + t.tex_block + 4) != 3 ||
      REX_LOAD_U32(src + t.tex_block + 8) != 0x3F800000u) {
    return 0;
  }
  uint32_t n = 0x200;  // hasta el siguiente descriptor
  for (uint32_t i = 0; i < kImages; ++i) {
    const uint32_t q = REX_LOAD_U32(tbl + 4 * i);
    if (q > src && q - src < n) n = q - src;
  }
  auto& b = g_images[vc * 2 + (name ? 1 : 0)];
  if (b.tpl == src && b.buf) return b.buf;
  if (!b.buf || b.cap < n) {
    b.buf = dbz3::roster::GuestAlloc(0x200);
    b.cap = 0x200;
    if (!b.buf) return 0;
  }
  for (uint32_t o = 0; o + 4 <= n; o += 4) {
    uint32_t v = REX_LOAD_U32(src + o);
    if (v >= src && v < src + n) v = v - src + b.buf;  // punteros internos
    REX_STORE_U32(b.buf + o, v);
  }
  auto f = [](float x) {
    uint32_t u;
    std::memcpy(&u, &x, 4);
    return u;
  };
  REX_STORE_U32(b.buf + t.tex_block, uint32_t(r[0]));
  for (int k = 0; k < 4; ++k) REX_STORE_U32(b.buf + t.tex_block + 0x10 + 4 * k, f(float(r[1 + k])));
  const float w = float(r[3] - r[1]) / 2, h = float(r[4] - r[2]) / 2;
  REX_STORE_U32(b.buf + 0x20, f(-w));
  REX_STORE_U32(b.buf + 0x24, f(-h));
  REX_STORE_U32(b.buf + 0x28, f(w));
  REX_STORE_U32(b.buf + 0x2C, f(h));
  b.tpl = src;
  return b.buf;
}

// ---- cambio de contexto: slot anfitrion -> personaje de la casilla nueva ----
thread_local int t_depth = 0;
thread_local int t_active = -1;
thread_local uint16_t t_saved_ids[3];
thread_local uint32_t t_name_slot = 0;   // entrada de la tabla de sprites cambiada
thread_local uint32_t t_name_saved = 0;
// lista "Custom" de capsulas (datos guardados por casilla: +68 + 14 * slot del bloque de
// la partida del jugador, estado +120): la del personaje nuevo en vez de la del anfitrion
thread_local uint32_t t_save_buf = 0;
thread_local uint32_t t_list_at = 0;
thread_local uint16_t t_host_list[7];
thread_local uint16_t t_own_list[7];
constexpr uint32_t kSaveCustom = 68;      // 38 x 7 x u16 por casilla
constexpr uint32_t kSaveInventory = 1094; // 2048 x u8 por capsula

void Restore(uint8_t* base) {
  if (t_active < 0) return;
  const auto& c = GetVirtualCell(t_active);
  if (t_list_at) {           // guarda lo editado (Edit Skills) y devuelve la del anfitrion
    uint16_t now[7];
    for (int k = 0; k < 7; ++k) now[k] = REX_LOAD_U16(t_list_at + 2 * k);
    if (std::memcmp(now, t_own_list, sizeof(now)) != 0) dbz3::roster::SetCustomList(c.id, now);
    for (int k = 0; k < 7; ++k) REX_STORE_U16(t_list_at + 2 * k, t_host_list[k]);
    t_list_at = 0;
  }
  for (int k = 0; k < 3; ++k) REX_STORE_U16(kSlotToId[k] + 2 * c.alias, t_saved_ids[k]);
  if (t_name_slot) REX_STORE_U32(t_name_slot, t_name_saved);
  t_name_slot = 0;
  t_active = -1;
}

void Apply(uint8_t* base, int vc) {
  if (vc == t_active) return;
  Restore(base);
  if (vc < 0) return;
  const auto& c = GetVirtualCell(vc);
  for (int k = 0; k < 3; ++k) {
    t_saved_ids[k] = REX_LOAD_U16(kSlotToId[k] + 2 * c.alias);
    REX_STORE_U16(kSlotToId[k] + 2 * c.alias, uint16_t(c.id));
  }
  if (GuestPtr(t_save_buf) && c.alias < kRandomSlot) {
    t_list_at = t_save_buf + kSaveCustom + 14 * c.alias;
    dbz3::roster::GetCustomList(c.id, t_own_list);
    for (int k = 0; k < 7; ++k) {
      t_host_list[k] = REX_LOAD_U16(t_list_at + 2 * k);
      REX_STORE_U16(t_list_at + 2 * k, t_own_list[k]);
    }
    dbz3::roster::OwnNewCapsules(t_save_buf + kSaveInventory);   // sus capsulas, siempre tuyas
  }
  const uint32_t sel = REX_LOAD_U32(kSelectGlobal);
  const uint32_t tbl = GuestPtr(sel) ? SpriteTable(base, REX_LOAD_U32(sel + 16)) : 0;
  if (const uint32_t desc = BuildImage(base, tbl, vc, true)) {
    t_name_slot = tbl + 4 * (kNameImageBase + c.alias);
    t_name_saved = REX_LOAD_U32(t_name_slot);
    REX_STORE_U32(t_name_slot, desc);
  }
  t_active = vc;
}

// r3 = task object; +48 = player state, or (nested: sub_82182210 / 82182930) a
// confirm-task state whose +16 is the player state.
void Enter(uint8_t* base, uint32_t obj, bool nested) {
  if (t_depth++ == 0 && VirtualCellCount() > 0 && GuestPtr(obj)) {
    uint32_t st = REX_LOAD_U32(obj + 48);
    if (nested && GuestPtr(st)) st = REX_LOAD_U32(st + 16);
    t_save_buf = GuestPtr(st) ? REX_LOAD_U32(st + 120) : 0;
    Apply(base, NewCellOfState(base, st));
  }
}

void Leave(uint8_t* base) {
  if (--t_depth == 0) Restore(base);
}

}  // namespace

#include "select_wheel_gen.inc"

REX_HOOK_RAW(sub_8217D710) { Wheel_8217D710(ctx, base); }
REX_HOOK_RAW(sub_8217DB20) { Wheel_8217DB20(ctx, base); }
REX_HOOK_RAW(sub_8217DC38) { Wheel_8217DC38(ctx, base); }
REX_HOOK_RAW(sub_8217E410) { Wheel_8217E410(ctx, base); }
// Creates a wheel object (returns it in r3; +48 = wheel data, 2368 B here).
REX_HOOK_RAW(sub_8217E6D8) {
  Wheel_8217E6D8(ctx, base);
  std::lock_guard<std::mutex> lk(g_mu);
  if (ctx.r3.u32) g_wheel_objs[ctx.r3.u32] = REX_LOAD_U32(ctx.r3.u32 + 48);
}

// Puts the cursor on the FIRST cell of slot r4 (r3 = wheel data); the select
// does it when a player confirms. A cursor on a new cell of that host slot stays
// on it (the host's own cells are hidden from the search).
REX_HOOK_RAW(sub_8217DE80) {
  const uint32_t d = ctx.r3.u32;
  const int vc = NewCellOfWheel(base, d);
  uint32_t hidden[kCells];
  uint32_t nh = 0;
  uint8_t alias = 0;
  if (vc >= 0 && int8_t(ctx.r4.s32) == int8_t(GetVirtualCell(vc).alias)) {
    alias = uint8_t(GetVirtualCell(vc).alias);
    const uint32_t cur = REX_LOAD_U32(d + 40);
    for (uint32_t at = d + kCellBase + 2; at < cur && nh < kCells; at += kCellSize) {
      if (REX_LOAD_U8(at) == alias) {
        REX_STORE_U8(at, 0x7F);
        hidden[nh++] = at;
      }
    }
  }
  Wheel_8217DE80(ctx, base);
  for (uint32_t k = 0; k < nh; ++k) REX_STORE_U8(hidden[k], alias);
}

// Rebuilds the wheel for a slot mask (r3 = wheel object, r4 = u64 mask).
REX_HOOK_RAW(sub_8217E490) {
  const uint32_t obj = ctx.r3.u32;
  const uint64_t mask = ctx.r4.u64;
  if (!obj) return;
  const uint32_t d = REX_LOAD_U32(obj + 48);
  int8_t cur_slot = 0;
  if (const uint32_t cur = REX_LOAD_U32(d + 40)) cur_slot = int8_t(REX_LOAD_U8(cur + 2));
  const int cur_vc = NewCellOfWheel(base, d);
  REX_STORE_U64(d + 16, mask);
  uint32_t n = 0;
  for (uint32_t s = 0; s < kRealSlots; ++s) n += (mask >> s) & 1;
  n += uint32_t(NewCellsFor(mask).size());
  REX_STORE_U8(d + 12, uint8_t(n));
  ctx.r3.u64 = d;
  sub_8217D940(ctx, base);
  REX_STORE_U32(d + 40, 0);
  std::memset(base + d + kCellBase, 0, kCells * kCellSize);
  std::memset(base + d + kPosBase, 0, kCells * 8);
  ctx.r3.u64 = d;
  sub_8217D710(ctx, base);
  ctx.r3.u64 = d;
  sub_8217E030(ctx, base);
  ctx.r3.u64 = d;
  sub_8217E090(ctx, base);
  if (cur_vc >= 0) {  // seguir en la casilla nueva tras reconstruir
    std::lock_guard<std::mutex> lk(g_mu);
    const auto& map = g_wheels[d];
    for (uint32_t k = 0; k < kCells; ++k) {
      if (map[k] == cur_vc) REX_STORE_U32(d + 40, d + kCellBase + kCellSize * k);
    }
  }
  ctx.r3.u64 = d;
  ctx.r4.s64 = cur_slot;
  sub_8217DE80(ctx, base);
  ctx.r3.u64 = d;
  sub_8217D870(ctx, base);
}

// Assigns a slot to every cell (r3 = wheel data): available slots in order, each
// new cell right after its `after` slot (else at the end), then the random cell.
REX_HOOK_RAW(sub_8217E030) {
  const uint32_t d = ctx.r3.u32;
  const uint64_t mask = REX_LOAD_U64(d + 16);
  std::array<int8_t, kCells> map;
  map.fill(-1);
  uint32_t n = 0;
  auto add = [&](uint32_t slot, int vc) {
    if (n >= kCells) return;
    REX_STORE_U8(d + kCellBase + kCellSize * n + 2, uint8_t(slot));
    map[n++] = int8_t(vc);
  };
  const std::vector<int> news = NewCellsFor(mask);
  std::vector<bool> placed(news.size(), false);
  for (uint32_t s = 0; s < kRandomSlot; ++s) {
    if (!((mask >> s) & 1)) continue;
    add(s, -1);
    for (size_t i = 0; i < news.size(); ++i) {  // casillas nuevas que van tras esta
      if (!placed[i] && GetVirtualCell(news[i]).after == s) {
        add(GetVirtualCell(news[i]).alias, news[i]);
        placed[i] = true;
      }
    }
  }
  for (size_t i = 0; i < news.size(); ++i) {
    if (!placed[i]) add(GetVirtualCell(news[i]).alias, news[i]);
  }
  if ((mask >> kRandomSlot) & 1) add(kRandomSlot, -1);
  {
    std::lock_guard<std::mutex> lk(g_mu);
    g_wheels[d] = map;
  }
  REX_STORE_U32(d + 40, d + kCellBase);
  sub_8217D870(ctx, base);
}

// Frees the icon / frame sprites of every cell (r3 = wheel data).
REX_HOOK_RAW(sub_8217D940) {
  const uint32_t d = ctx.r3.u32;
  for (uint32_t k = 0; k < kCells; ++k) {
    for (uint32_t off : {4u, 8u}) {
      const uint32_t at = d + kCellBase + kCellSize * k + off;
      if (const uint32_t sprite = REX_LOAD_U32(at)) {
        ctx.r3.u64 = sprite;
        ctx.r4.u64 = 1;
        sub_820ACCF0(ctx, base);
        REX_STORE_U32(at, 0);
      }
    }
  }
}

// Cursor changed (r3 = wheel data): copies the cell's per-slot data to the player
// block. Inside a player's select logic, re-evaluate the new-cell context.
REX_HOOK_RAW(sub_8217D870) {
  const uint32_t d = ctx.r3.u32;
  __imp__sub_8217D870(ctx, base);
  if (t_depth > 0) Apply(base, NewCellOfWheel(base, d));
}

// Select data -> save (r3 = select data: +68 custom capsules per slot, +1094 inventory;
// called through a pointer): while a new character's own list is swapped in, the save
// must get the host slot's list.
REX_HOOK_RAW(sub_82179880) {
  const bool swapped = t_list_at && ctx.r3.u32 == t_save_buf;
  uint16_t own[7];
  if (swapped) {
    for (int k = 0; k < 7; ++k) {
      own[k] = REX_LOAD_U16(t_list_at + 2 * k);
      REX_STORE_U16(t_list_at + 2 * k, t_host_list[k]);
    }
  }
  __imp__sub_82179880(ctx, base);
  if (swapped) for (int k = 0; k < 7; ++k) REX_STORE_U16(t_list_at + 2 * k, own[k]);
}

// Per-player select states (r3 = task object, +48 = player state).
#define DBZ3_SELECT_PLAYER_HANDLER(fn, nested) \
  REX_HOOK_RAW(fn) {                           \
    Enter(base, ctx.r3.u32, nested);           \
    __imp__##fn(ctx, base);                    \
    Leave(base);                               \
  }
DBZ3_SELECT_PLAYER_HANDLER(sub_8217CB10, false)
DBZ3_SELECT_PLAYER_HANDLER(sub_8217CC68, false)
DBZ3_SELECT_PLAYER_HANDLER(sub_8217CFC8, false)
DBZ3_SELECT_PLAYER_HANDLER(sub_82180E90, false)
DBZ3_SELECT_PLAYER_HANDLER(sub_82182210, true)
DBZ3_SELECT_PLAYER_HANDLER(sub_82182930, true)
#undef DBZ3_SELECT_PLAYER_HANDLER

REX_HOOK_RAW(sub_82180AA0) {
  dbz3_trace_sub_82180AA0(ctx, base);
  Enter(base, ctx.r3.u32, false);
  __imp__sub_82180AA0(ctx, base);
  Leave(base);
}

// Portrait request (r3 = portrait object, r4 = slot): remember which new cell
// asked for it; the portrait loads later in its own task (sub_8217F3F0).
REX_HOOK_RAW(sub_8217F520) {
  dbz3_trace_sub_8217F520(ctx, base);
  if (ctx.r3.u32 && VirtualCellCount() > 0) {
    std::lock_guard<std::mutex> lk(g_mu);
    g_portrait_obj[ctx.r3.u32] = t_active;
  }
  __imp__sub_8217F520(ctx, base);
}

// Portrait load: fid = table[slot][variant] (u32 [39][2]).
REX_HOOK_RAW(sub_8217F3F0) {
  dbz3_trace_sub_8217F3F0(ctx, base);
  int vc = -1;
  if (VirtualCellCount() > 0) {
    std::lock_guard<std::mutex> lk(g_mu);
    auto it = g_portrait_obj.find(ctx.r3.u32);
    if (it != g_portrait_obj.end()) vc = it->second;
  }
  if (vc < 0 || GetVirtualCell(vc).portrait[0] == 0xFFFFFFFFu) {
    __imp__sub_8217F3F0(ctx, base);
    return;
  }
  const auto& c = GetVirtualCell(vc);
  const uint32_t at = kPortraits + 8 * c.alias;
  const uint32_t old0 = REX_LOAD_U32(at), old1 = REX_LOAD_U32(at + 4);
  REX_STORE_U32(at, c.portrait[0]);
  REX_STORE_U32(at + 4, c.portrait[1]);
  __imp__sub_8217F3F0(ctx, base);
  REX_STORE_U32(at, old0);
  REX_STORE_U32(at + 4, old1);
}

// Creates the icon / frame sprites of every cell (r3 = wheel data); new cells
// get their own icon image.
REX_HOOK_RAW(sub_8217E090) {
  const uint32_t d = ctx.r3.u32;
  __imp__sub_8217E090(ctx, base);
  if (VirtualCellCount() == 0) return;
  std::array<int8_t, kCells> map;
  {
    std::lock_guard<std::mutex> lk(g_mu);
    auto it = g_wheels.find(d);
    if (it == g_wheels.end()) return;
    map = it->second;
  }
  const uint32_t tbl = SpriteTable(base, REX_LOAD_U32(d));
  const uint32_t n = std::min<uint32_t>(REX_LOAD_U8(d + 12), kCells);
  for (uint32_t k = 0; k < n; ++k) {
    if (map[k] < 0) continue;
    const uint32_t desc = BuildImage(base, tbl, map[k], false);
    if (!desc) continue;
    const uint32_t at = d + kCellBase + kCellSize * k + 4;
    if (const uint32_t old = REX_LOAD_U32(at)) {
      ctx.r3.u64 = old;
      ctx.r4.u64 = 1;
      sub_820ACCF0(ctx, base);
    }
    const uint32_t scale = REX_LOAD_U32(kSpriteScale);
    float fs;
    std::memcpy(&fs, &scale, 4);
    ctx.f1.f64 = double(fs);
    ctx.r3.u64 = desc;
    sub_820B06E0(ctx, base);
    REX_STORE_U32(at, ctx.r3.u32);
  }
}
