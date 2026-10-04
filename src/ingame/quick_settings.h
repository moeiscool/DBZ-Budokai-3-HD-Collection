// dbz3 - In-game quick settings (F1 / Back + Start): the SDK's controller menu
// (ported from DBZ Burst Limit Recompiled) filled with the launcher's own
// settings, so both stay in sync and everything is saved to dbz3_user.toml.

#pragma once

#include <functional>

#include <rex/ui/overlay/quick_menu.h>

namespace dbz3::ingame {

// open_full_settings: opens the full launcher dialog (the F4 settings).
void ConfigureQuickMenu(rex::ui::QuickMenuConfig& menu, std::function<void()> open_full_settings);

}  // namespace dbz3::ingame
