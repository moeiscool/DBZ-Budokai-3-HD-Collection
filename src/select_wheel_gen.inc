// GENERADO por tools/gen_select_wheel.py a partir de generated/ (US). NO EDITAR.
// Funciones de la rueda del select con la estructura ampliada a 64 celdas
// (posiciones 1136 -> 1840, tamano 1448 -> 2368). Los ganchos estan en select_ext.cpp.

static void Wheel_8217D710(PPCContext& ctx, uint8_t* base) {
	uint32_t ea{};
	ctx.r12.u64 = ctx.lr;
	ctx.lr = 0x8217D718;
	__savegprlr_29(ctx, base);
	ctx.r11.u64 = REX_LOAD_U8(ctx.r3.u32 + 12);
	ctx.r31.s64 = 1;
	ctx.r11.s64 = ctx.r11.s8;
	ctx.r8.u64 = ctx.r31.u64;
	ctx.r10.s64 = ctx.r11.s64 + -1;
	ctx.cr6.compare<int32_t>(ctx.r11.s32, 6, ctx.xer);
	ctx.r11.s64 = ctx.r10.s16;
	ctx.r30.u64 = ctx.r11.u64;
	if (ctx.cr6.lt) goto loc_8217D74C;
	ctx.r10.u64 = REX_LOAD_U8(ctx.r3.u32 + 12);
	ctx.r10.s64 = ctx.r10.s8;
	ctx.cr6.compare<int32_t>(ctx.r10.s32, 8, ctx.xer);
	if (!ctx.cr6.lt) goto loc_8217D754;
loc_8217D74C:
	ctx.r4.s64 = 4608;
	goto loc_8217D774;
loc_8217D754:
	ctx.cr6.compare<int32_t>(ctx.r10.s32, 10, ctx.xer);
	if (!ctx.cr6.lt) goto loc_8217D764;
	ctx.r4.s64 = 4096;
	goto loc_8217D774;
loc_8217D764:
	ctx.cr6.compare<int32_t>(ctx.r10.s32, 12, ctx.xer);
	ctx.r4.s64 = 3328;
	if (ctx.cr6.lt) goto loc_8217D774;
	ctx.r4.s64 = 2816;
loc_8217D774:
	ctx.r7.s64 = 0;
	REX_STORE_U16(ctx.r3.u32 + 1842, ctx.r31.u16);
	ctx.r5.s64 = ctx.r11.s16;
	ctx.cr0.compare<int32_t>(ctx.r5.s32, 0, ctx.xer);
	ctx.r6.s64 = ctx.r3.s64 + 1840;
	REX_STORE_U32(ctx.r3.u32 + 1844, ctx.r7.u32);
	ctx.r11.s64 = 2;
	if (!ctx.cr0.gt) goto loc_8217D840;
loc_8217D790:
	ctx.r9.s64 = ctx.r11.s16;
	ctx.r10.u64 = ctx.r11.u32 & 0x1;
	ctx.cr0.compare<int32_t>(ctx.r10.s32, 0, ctx.xer);
	ctx.cr6.compare<int32_t>(ctx.r9.s32, 17, ctx.xer);
	if (!ctx.cr0.eq) goto loc_8217D7DC;
	ctx.r10.s64 = ctx.r8.s16;
	ctx.r11.s64 = ctx.r10.s64 + 230;
	ctx.r10.s64 = ctx.r10.s64 + 1;
	ctx.r11.u64 = __builtin_rotateleft64(ctx.r11.u32 | (ctx.r11.u64 << 32), 3) & 0xFFFFFFF8;
	ctx.r11.u64 = ctx.r11.u64 + ctx.r3.u64;
	if (!ctx.cr6.lt) goto loc_8217D7CC;
	ctx.xer.ca = (ctx.r9.s32 < 0) & ((ctx.r9.u32 & 0x1) != 0);
	ctx.r8.s64 = ctx.r9.s32 >> 1;
	REX_STORE_U16(ctx.r11.u32 + 2, ctx.r31.u16);
	ctx.r8.s64 = int64_t(ctx.r8.s32) * int64_t(ctx.r4.s32);
	REX_STORE_U32(ctx.r11.u32 + 4, ctx.r8.u32);
	goto loc_8217D7D4;
loc_8217D7CC:
	REX_STORE_U16(ctx.r11.u32 + 2, ctx.r7.u16);
	REX_STORE_U32(ctx.r11.u32 + 4, ctx.r7.u32);
loc_8217D7D4:
	ctx.r8.s64 = ctx.r10.s16;
	goto loc_8217D828;
loc_8217D7DC:
	ctx.r10.s64 = ctx.r30.s16;
	ctx.r11.s64 = ctx.r10.s64 + 230;
	ctx.r11.u64 = __builtin_rotateleft64(ctx.r11.u32 | (ctx.r11.u64 << 32), 3) & 0xFFFFFFF8;
	ctx.r11.u64 = ctx.r11.u64 + ctx.r3.u64;
	if (!ctx.cr6.lt) goto loc_8217D814;
	ctx.xer.ca = (ctx.r9.s32 < 0) & ((ctx.r9.u32 & 0x1) != 0);
	ctx.r30.s64 = ctx.r9.s32 >> 1;
	REX_STORE_U16(ctx.r11.u32 + 2, ctx.r31.u16);
	ctx.r29.s64 = 65536;
	ctx.r30.s64 = int64_t(ctx.r30.s32) * int64_t(ctx.r4.s32);
	ctx.r30.u64 = ctx.r29.u64 - ctx.r30.u64;
	ctx.r10.s64 = ctx.r10.s64 + -1;
	REX_STORE_U32(ctx.r11.u32 + 4, ctx.r30.u32);
	ctx.r30.s64 = ctx.r10.s16;
	goto loc_8217D828;
loc_8217D814:
	REX_STORE_U16(ctx.r11.u32 + 2, ctx.r7.u16);
	ctx.r10.u64 = ctx.r8.u64;
	REX_STORE_U32(ctx.r11.u32 + 4, ctx.r7.u32);
	ctx.r11.s64 = ctx.r8.s64 + 1;
	ctx.r8.s64 = ctx.r11.s16;
loc_8217D828:
	ctx.r11.s64 = ctx.r5.s64 + -1;
	ctx.r10.s64 = ctx.r9.s64 + 1;
	ctx.r9.s64 = ctx.r11.s16;
	ctx.r11.s64 = ctx.r10.s16;
	ctx.r5.u64 = ctx.r9.u64;
	ctx.cr0.compare<int32_t>(ctx.r5.s32, 0, ctx.xer);
	if (ctx.cr0.gt) goto loc_8217D790;
loc_8217D840:
	ctx.r10.u64 = REX_LOAD_U8(ctx.r3.u32 + 12);
	ctx.r11.u64 = ctx.r7.u64;
	ctx.r10.s64 = ctx.r10.s8;
	ctx.cr0.compare<int32_t>(ctx.r10.s32, 0, ctx.xer);
	if (!ctx.cr0.gt) goto loc_8217D86C;
	ctx.r10.s64 = ctx.r6.s64 + -8;
loc_8217D854:
	ea = 8 + ctx.r10.u32;
	REX_STORE_U16(ea, ctx.r31.u16);
	ctx.r10.u32 = ea;
	ctx.r11.s64 = ctx.r11.s64 + 1;
	ctx.r9.u64 = REX_LOAD_U8(ctx.r3.u32 + 12);
	ctx.r9.s64 = ctx.r9.s8;
	ctx.cr6.compare<int32_t>(ctx.r11.s32, ctx.r9.s32, ctx.xer);
	if (ctx.cr6.lt) goto loc_8217D854;
loc_8217D86C:
	__restgprlr_29(ctx, base);
	return;
}

static void Wheel_8217DB20(PPCContext& ctx, uint8_t* base) {
	PPCRegister temp{};
	ctx.r11.u64 = REX_LOAD_U8(ctx.r3.u32 + 12);
	ctx.r5.s64 = 0;
	ctx.r11.s64 = ctx.r11.s8;
	ctx.cr0.compare<int32_t>(ctx.r11.s32, 0, ctx.xer);
	ctx.r7.u64 = ctx.r5.u64;
	if (!ctx.cr0.gt) goto loc_8217DC24;
	ctx.r11.s64 = ctx.r3.s64 + 56;
	ctx.r6.s64 = -2110193664;
loc_8217DB3C:
	ctx.r9.u64 = REX_LOAD_U8(ctx.r11.u32 + 0);
	ctx.r10.s64 = ctx.r9.s8;
	ctx.cr0.compare<int32_t>(ctx.r10.s32, 0, ctx.xer);
	ctx.r8.s64 = ctx.r9.s8;
	if (!ctx.cr0.eq) goto loc_8217DB54;
	ctx.r10.u64 = REX_LOAD_U8(ctx.r3.u32 + 12);
	ctx.r10.s64 = ctx.r10.s8;
loc_8217DB54:
	ctx.r10.s64 = ctx.r10.s64 + -1;
	ctx.r10.s64 = ctx.r10.s16;
	ctx.r9.s64 = ctx.r10.s8;
	ctx.cr0.compare<int32_t>(ctx.r9.s32, 0, ctx.xer);
	REX_STORE_U8(ctx.r11.u32 + 0, ctx.r9.u8);
	if (!ctx.cr0.eq) goto loc_8217DB70;
	ctx.r9.s64 = ctx.r11.s64 + -12;
	REX_STORE_U32(ctx.r3.u32 + 40, ctx.r9.u32);
loc_8217DB70:
	ctx.r10.s64 = ctx.r10.s16;
	ctx.r10.u64 = __builtin_rotateleft64(ctx.r10.u32 | (ctx.r10.u64 << 32), 3) & 0xFFFFFFF8;
	ctx.r9.u64 = ctx.r10.u64 + ctx.r3.u64;
	ctx.r10.u64 = REX_LOAD_U16(ctx.r9.u32 + 1842);
	ctx.cr0.compare<uint32_t>(ctx.r10.u32, 0, ctx.xer);
	if (!ctx.cr0.eq) goto loc_8217DB90;
	REX_STORE_U8(ctx.r11.u32 + 1, ctx.r5.u8);
	goto loc_8217DC0C;
loc_8217DB90:
	ctx.r10.s64 = ctx.r8.s16;
	ctx.r8.s64 = 1;
	ctx.r10.u64 = __builtin_rotateleft64(ctx.r10.u32 | (ctx.r10.u64 << 32), 3) & 0xFFFFFFF8;
	REX_STORE_U8(ctx.r11.u32 + 1, ctx.r8.u8);
	ctx.r10.u64 = ctx.r10.u64 + ctx.r3.u64;
	ctx.r8.u64 = REX_LOAD_U16(ctx.r10.u32 + 1842);
	ctx.cr0.compare<uint32_t>(ctx.r8.u32, 0, ctx.xer);
	if (!ctx.cr0.eq) goto loc_8217DBC0;
	ctx.r10.u64 = REX_LOAD_U32(ctx.r9.u32 + 1844);
	REX_STORE_U16(ctx.r11.u32 + 2, ctx.r5.u16);
	REX_STORE_U32(ctx.r11.u32 + 4, ctx.r10.u32);
	goto loc_8217DC0C;
loc_8217DBC0:
	ctx.r10.u64 = REX_LOAD_U32(ctx.r10.u32 + 1844);
	ctx.r9.u64 = REX_LOAD_U32(ctx.r9.u32 + 1844);
	ctx.cr6.compare<int32_t>(ctx.r9.s32, ctx.r10.s32, ctx.xer);
	if (!ctx.cr6.gt) goto loc_8217DBD4;
	ctx.r10.s64 = ctx.r10.s64 + 65536;
loc_8217DBD4:
	ctx.r10.u64 = ctx.r9.u64 - ctx.r10.u64;
	ctx.fpscr.disableFlushMode();
	temp.u32 = REX_LOAD_U32(ctx.r6.u32 + -23028);
	ctx.f0.f64 = double(temp.f32);
	ctx.r9.s64 = 12;
	ctx.r10.u64 = uint32_t((ctx.r9.s32 && !(ctx.r10.s32 == INT32_MIN && ctx.r9.s32 == -1)) ? ctx.r10.s32 / ctx.r9.s32 : 0);
	ctx.r10.s64 = ctx.r10.s32;
	REX_STORE_U64(ctx.r1.u32 + -16, ctx.r10.u64);
	ctx.f13.u64 = REX_LOAD_U64(ctx.r1.u32 + -16);
	ctx.f13.f64 = double(ctx.f13.s64);
	ctx.f13.f64 = double(float(ctx.f13.f64));
	ctx.f0.f64 = double(float(ctx.f13.f64 * ctx.f0.f64));
	ctx.f0.s64 = std::isnan(ctx.f0.f64) ? int64_t(0x80000000U) : (ctx.f0.f64 >= double(INT_MAX)) ? INT_MAX : simde_mm_cvttsd_si32(simde_mm_load_sd(&ctx.f0.f64));
	REX_STORE_U64(ctx.r1.u32 + -8, ctx.f0.u64);
	ctx.r10.u64 = REX_LOAD_U16(ctx.r1.u32 + -2);
	REX_STORE_U16(ctx.r11.u32 + 2, ctx.r10.u16);
loc_8217DC0C:
	ctx.r10.u64 = REX_LOAD_U8(ctx.r3.u32 + 12);
	ctx.r7.s64 = ctx.r7.s64 + 1;
	ctx.r11.s64 = ctx.r11.s64 + 28;
	ctx.r10.s64 = ctx.r10.s8;
	ctx.cr6.compare<int32_t>(ctx.r7.s32, ctx.r10.s32, ctx.xer);
	if (ctx.cr6.lt) goto loc_8217DB3C;
loc_8217DC24:
	ctx.r11.s64 = -2113798144;
	ctx.fpscr.disableFlushMode();
	temp.u32 = REX_LOAD_U32(ctx.r11.u32 + -7704);
	ctx.f0.f64 = double(temp.f32);
	temp.f32 = float(ctx.f0.f64);
	REX_STORE_U32(ctx.r3.u32 + 32, temp.u32);
	return;
}

static void Wheel_8217DC38(PPCContext& ctx, uint8_t* base) {
	PPCRegister temp{};
	ctx.r11.u64 = REX_LOAD_U8(ctx.r3.u32 + 12);
	ctx.r5.s64 = 0;
	ctx.r11.s64 = ctx.r11.s8;
	ctx.cr0.compare<int32_t>(ctx.r11.s32, 0, ctx.xer);
	ctx.r7.u64 = ctx.r5.u64;
	if (!ctx.cr0.gt) goto loc_8217DD4C;
	ctx.r11.s64 = ctx.r3.s64 + 56;
	ctx.r6.s64 = -2110193664;
loc_8217DC54:
	ctx.r10.u64 = REX_LOAD_U8(ctx.r3.u32 + 12);
	ctx.r8.u64 = REX_LOAD_U8(ctx.r11.u32 + 0);
	ctx.r9.s64 = ctx.r10.s8;
	ctx.r10.s64 = ctx.r8.s8;
	ctx.r4.s64 = ctx.r9.s64 + -1;
	ctx.r9.s64 = ctx.r8.s8;
	ctx.cr6.compare<int32_t>(ctx.r10.s32, ctx.r4.s32, ctx.xer);
	if (!ctx.cr6.eq) goto loc_8217DC7C;
	ctx.r10.u64 = ctx.r5.u64;
	goto loc_8217DC84;
loc_8217DC7C:
	ctx.r10.s64 = ctx.r10.s64 + 1;
	ctx.r10.s64 = ctx.r10.s16;
loc_8217DC84:
	ctx.r8.s64 = ctx.r10.s8;
	ctx.cr0.compare<int32_t>(ctx.r8.s32, 0, ctx.xer);
	REX_STORE_U8(ctx.r11.u32 + 0, ctx.r8.u8);
	if (!ctx.cr0.eq) goto loc_8217DC98;
	ctx.r8.s64 = ctx.r11.s64 + -12;
	REX_STORE_U32(ctx.r3.u32 + 40, ctx.r8.u32);
loc_8217DC98:
	ctx.r10.s64 = ctx.r10.s16;
	ctx.r10.u64 = __builtin_rotateleft64(ctx.r10.u32 | (ctx.r10.u64 << 32), 3) & 0xFFFFFFF8;
	ctx.r8.u64 = ctx.r10.u64 + ctx.r3.u64;
	ctx.r10.u64 = REX_LOAD_U16(ctx.r8.u32 + 1842);
	ctx.cr0.compare<uint32_t>(ctx.r10.u32, 0, ctx.xer);
	if (!ctx.cr0.eq) goto loc_8217DCB8;
	REX_STORE_U8(ctx.r11.u32 + 1, ctx.r5.u8);
	goto loc_8217DD34;
loc_8217DCB8:
	ctx.r10.s64 = ctx.r9.s16;
	ctx.r9.s64 = 1;
	ctx.r10.u64 = __builtin_rotateleft64(ctx.r10.u32 | (ctx.r10.u64 << 32), 3) & 0xFFFFFFF8;
	REX_STORE_U8(ctx.r11.u32 + 1, ctx.r9.u8);
	ctx.r10.u64 = ctx.r10.u64 + ctx.r3.u64;
	ctx.r9.u64 = REX_LOAD_U16(ctx.r10.u32 + 1842);
	ctx.cr0.compare<uint32_t>(ctx.r9.u32, 0, ctx.xer);
	if (!ctx.cr0.eq) goto loc_8217DCE8;
	ctx.r10.u64 = REX_LOAD_U32(ctx.r8.u32 + 1844);
	REX_STORE_U16(ctx.r11.u32 + 2, ctx.r5.u16);
	REX_STORE_U32(ctx.r11.u32 + 4, ctx.r10.u32);
	goto loc_8217DD34;
loc_8217DCE8:
	ctx.r9.u64 = REX_LOAD_U32(ctx.r10.u32 + 1844);
	ctx.r10.u64 = REX_LOAD_U32(ctx.r8.u32 + 1844);
	ctx.cr6.compare<int32_t>(ctx.r10.s32, ctx.r9.s32, ctx.xer);
	if (!ctx.cr6.lt) goto loc_8217DCFC;
	ctx.r10.s64 = ctx.r10.s64 + 65536;
loc_8217DCFC:
	ctx.r10.u64 = ctx.r10.u64 - ctx.r9.u64;
	ctx.fpscr.disableFlushMode();
	temp.u32 = REX_LOAD_U32(ctx.r6.u32 + -23028);
	ctx.f0.f64 = double(temp.f32);
	ctx.r9.s64 = 12;
	ctx.r10.u64 = uint32_t((ctx.r9.s32 && !(ctx.r10.s32 == INT32_MIN && ctx.r9.s32 == -1)) ? ctx.r10.s32 / ctx.r9.s32 : 0);
	ctx.r10.s64 = ctx.r10.s32;
	REX_STORE_U64(ctx.r1.u32 + -16, ctx.r10.u64);
	ctx.f13.u64 = REX_LOAD_U64(ctx.r1.u32 + -16);
	ctx.f13.f64 = double(ctx.f13.s64);
	ctx.f13.f64 = double(float(ctx.f13.f64));
	ctx.f0.f64 = double(float(ctx.f13.f64 * ctx.f0.f64));
	ctx.f0.s64 = std::isnan(ctx.f0.f64) ? int64_t(0x80000000U) : (ctx.f0.f64 >= double(INT_MAX)) ? INT_MAX : simde_mm_cvttsd_si32(simde_mm_load_sd(&ctx.f0.f64));
	REX_STORE_U64(ctx.r1.u32 + -8, ctx.f0.u64);
	ctx.r10.u64 = REX_LOAD_U16(ctx.r1.u32 + -2);
	REX_STORE_U16(ctx.r11.u32 + 2, ctx.r10.u16);
loc_8217DD34:
	ctx.r10.u64 = REX_LOAD_U8(ctx.r3.u32 + 12);
	ctx.r7.s64 = ctx.r7.s64 + 1;
	ctx.r11.s64 = ctx.r11.s64 + 28;
	ctx.r10.s64 = ctx.r10.s8;
	ctx.cr6.compare<int32_t>(ctx.r7.s32, ctx.r10.s32, ctx.xer);
	if (ctx.cr6.lt) goto loc_8217DC54;
loc_8217DD4C:
	ctx.r11.s64 = -2113798144;
	ctx.fpscr.disableFlushMode();
	temp.u32 = REX_LOAD_U32(ctx.r11.u32 + -7704);
	ctx.f0.f64 = double(temp.f32);
	temp.f32 = float(ctx.f0.f64);
	REX_STORE_U32(ctx.r3.u32 + 32, temp.u32);
	return;
}

static void Wheel_8217DE80(PPCContext& ctx, uint8_t* base) {
	PPCRegister temp{};
	uint32_t ea{};
	ctx.r12.u64 = ctx.lr;
	ctx.lr = 0x8217DE88;
	__savegprlr_28(ctx, base);
	ea = -128 + ctx.r1.u32;
	REX_STORE_U32(ea, ctx.r1.u32);
	ctx.r1.u32 = ea;
	ctx.r11.u64 = REX_LOAD_U8(ctx.r3.u32 + 12);
	ctx.r30.u64 = ctx.r3.u64;
	ctx.r10.s64 = 0;
	ctx.r11.s64 = ctx.r11.s8;
	ctx.cr0.compare<int32_t>(ctx.r11.s32, 0, ctx.xer);
	if (!ctx.cr0.gt) goto loc_8217DFA0;
	ctx.r9.s64 = ctx.r4.s16;
	ctx.r11.s64 = ctx.r3.s64 + 46;
loc_8217DEA8:
	ctx.r8.u64 = REX_LOAD_U8(ctx.r11.u32 + 0);
	ctx.r8.s64 = ctx.r8.s8;
	ctx.cr6.compare<int32_t>(ctx.r8.s32, ctx.r9.s32, ctx.xer);
	if (ctx.cr6.eq) goto loc_8217DED4;
	ctx.r8.u64 = REX_LOAD_U8(ctx.r30.u32 + 12);
	ctx.r10.s64 = ctx.r10.s64 + 1;
	ctx.r11.s64 = ctx.r11.s64 + 28;
	ctx.r8.s64 = ctx.r8.s8;
	ctx.cr6.compare<int32_t>(ctx.r10.s32, ctx.r8.s32, ctx.xer);
	if (ctx.cr6.lt) goto loc_8217DEA8;
	goto loc_8217DFA0;
loc_8217DED4:
	ctx.r11.s64 = static_cast<int64_t>(ctx.r10.u64 * static_cast<uint64_t>(28));
	ctx.r11.u64 = ctx.r11.u64 + ctx.r30.u64;
	ctx.xer.ca = ctx.r11.u32 > 4294967251;
	ctx.r11.s64 = ctx.r11.s64 + 44;
	ctx.cr0.compare<int32_t>(ctx.r11.s32, 0, ctx.xer);
	if (ctx.cr0.eq) goto loc_8217DFA0;
	REX_STORE_U32(ctx.r30.u32 + 40, ctx.r11.u32);
	ctx.r29.s64 = 0;
	ctx.r11.u64 = REX_LOAD_U8(ctx.r11.u32 + 12);
	ctx.r11.s64 = ctx.r11.s8;
	ctx.r28.s64 = static_cast<int64_t>(-ctx.r11.u64);
	ctx.r31.s64 = ctx.r30.s64 + 56;
loc_8217DEFC:
	ctx.r11.u64 = REX_LOAD_U8(ctx.r30.u32 + 12);
	ctx.r9.s64 = 0;
	ctx.r10.u64 = REX_LOAD_U8(ctx.r31.u32 + 0);
	ctx.r3.s64 = ctx.r31.s64 + -12;
	ctx.r11.s64 = ctx.r11.s8;
	ctx.r10.s64 = ctx.r10.s8;
	if (ctx.r11.s32 == 0 || ctx.r11.u32 < 0u) ppc_trap(ctx, base, 0);
	ctx.r10.u64 = ctx.r10.u64 + ctx.r11.u64;
	ctx.r8.u64 = ctx.r10.u64 + ctx.r28.u64;
	ctx.r7.u64 = uint32_t((ctx.r11.s32 && !(ctx.r8.s32 == INT32_MIN && ctx.r11.s32 == -1)) ? ctx.r8.s32 / ctx.r11.s32 : 0);
	ctx.r10.u64 = __builtin_rotateleft32(ctx.r8.u32, 1);
	ctx.r7.s64 = int64_t(ctx.r7.s32) * int64_t(ctx.r11.s32);
	ctx.r8.u64 = ctx.r8.u64 - ctx.r7.u64;
	ctx.r10.s64 = ctx.r10.s64 + -1;
	ctx.r8.s64 = ctx.r8.s8;
	ctx.r7.u64 = ctx.r11.u64 & ~ctx.r10.u64;
	ctx.r10.u64 = ctx.r8.u32 & 0xFF;
	REX_STORE_U8(ctx.r31.u32 + 0, ctx.r8.u8);
	ctx.r11.u64 = ctx.r8.u64;
	ctx.r8.s64 = ctx.r10.s8;
	ctx.r10.u64 = __builtin_rotateleft64(ctx.r11.u32 | (ctx.r11.u64 << 32), 3) & 0xFFFFFFF8;
	ctx.r11.u64 = __builtin_rotateleft64(ctx.r8.u32 | (ctx.r8.u64 << 32), 3) & 0xFFFFFFF8;
	ctx.r10.u64 = ctx.r10.u64 + ctx.r30.u64;
	ctx.r11.u64 = ctx.r11.u64 + ctx.r30.u64;
	if (ctx.r7.s32 == -1 || ctx.r7.u32 > 4294967295u) ppc_trap(ctx, base, 0);
	ctx.r10.u64 = REX_LOAD_U32(ctx.r10.u32 + 1844);
	REX_STORE_U32(ctx.r31.u32 + 4, ctx.r10.u32);
	REX_STORE_U16(ctx.r31.u32 + 2, ctx.r9.u16);
	ctx.r11.u64 = REX_LOAD_U16(ctx.r11.u32 + 1842);
	REX_STORE_U8(ctx.r31.u32 + 1, ctx.r11.u8);
	ctx.r4.u64 = REX_LOAD_U8(ctx.r30.u32 + 9);
	ctx.lr = 0x8217DF7C;
	sub_8217D9A0(ctx, base);
	ctx.r11.u64 = REX_LOAD_U8(ctx.r30.u32 + 12);
	ctx.r29.s64 = ctx.r29.s64 + 1;
	ctx.r31.s64 = ctx.r31.s64 + 28;
	ctx.r11.s64 = ctx.r11.s8;
	ctx.cr6.compare<int32_t>(ctx.r29.s32, ctx.r11.s32, ctx.xer);
	if (ctx.cr6.lt) goto loc_8217DEFC;
	ctx.r11.s64 = -2113798144;
	ctx.fpscr.disableFlushMode();
	temp.u32 = REX_LOAD_U32(ctx.r11.u32 + -2548);
	ctx.f0.f64 = double(temp.f32);
	temp.f32 = float(ctx.f0.f64);
	REX_STORE_U32(ctx.r30.u32 + 32, temp.u32);
loc_8217DFA0:
	ctx.r1.s64 = ctx.r1.s64 + 128;
	__restgprlr_28(ctx, base);
	return;
}

static void Wheel_8217E410(PPCContext& ctx, uint8_t* base) {
	uint32_t ea{};
	ctx.r12.u64 = ctx.lr;
	ctx.lr = 0x8217E418;
	__savegprlr_29(ctx, base);
	ea = -112 + ctx.r1.u32;
	REX_STORE_U32(ea, ctx.r1.u32);
	ctx.r1.u32 = ea;
	ctx.r11.u64 = REX_LOAD_U8(ctx.r3.u32 + 12);
	ctx.r30.u64 = ctx.r3.u64;
	ctx.r29.s64 = 0;
	ctx.r11.s64 = ctx.r11.s8;
	ctx.cr0.compare<int32_t>(ctx.r11.s32, 0, ctx.xer);
	if (!ctx.cr0.gt) goto loc_8217E484;
	ctx.r31.s64 = ctx.r3.s64 + 60;
loc_8217E434:
	ctx.r11.u64 = REX_LOAD_U16(ctx.r31.u32 + -16);
	ctx.r3.s64 = ctx.r31.s64 + -16;
	ctx.cr0.compare<uint32_t>(ctx.r11.u32, 0, ctx.xer);
	if (ctx.cr0.eq) goto loc_8217E46C;
	ctx.r11.u64 = REX_LOAD_U8(ctx.r31.u32 + -4);
	ctx.r10.s64 = 0;
	ctx.r11.s64 = ctx.r11.s8;
	ctx.r11.u64 = __builtin_rotateleft64(ctx.r11.u32 | (ctx.r11.u64 << 32), 3) & 0xFFFFFFF8;
	ctx.r11.u64 = ctx.r11.u64 + ctx.r30.u64;
	ctx.r11.u64 = REX_LOAD_U32(ctx.r11.u32 + 1844);
	REX_STORE_U16(ctx.r31.u32 + -2, ctx.r10.u16);
	REX_STORE_U32(ctx.r31.u32 + 0, ctx.r11.u32);
	ctx.r4.u64 = REX_LOAD_U8(ctx.r30.u32 + 9);
	ctx.lr = 0x8217E46C;
	sub_8217D9A0(ctx, base);
loc_8217E46C:
	ctx.r11.u64 = REX_LOAD_U8(ctx.r30.u32 + 12);
	ctx.r29.s64 = ctx.r29.s64 + 1;
	ctx.r31.s64 = ctx.r31.s64 + 28;
	ctx.r11.s64 = ctx.r11.s8;
	ctx.cr6.compare<int32_t>(ctx.r29.s32, ctx.r11.s32, ctx.xer);
	if (ctx.cr6.lt) goto loc_8217E434;
loc_8217E484:
	ctx.r1.s64 = ctx.r1.s64 + 112;
	__restgprlr_29(ctx, base);
	return;
}

static void Wheel_8217E6D8(PPCContext& ctx, uint8_t* base) {
	uint32_t ea{};
	ctx.r12.u64 = ctx.lr;
	ctx.lr = 0x8217E6E0;
	__savegprlr_23(ctx, base);
	ea = -160 + ctx.r1.u32;
	REX_STORE_U32(ea, ctx.r1.u32);
	ctx.r1.u32 = ea;
	ctx.r26.u64 = ctx.r9.u64;
	ctx.r25.u64 = ctx.r10.u64;
	ctx.r11.u64 = ctx.r8.u64;
	ctx.r10.s64 = -2113798144;
	ctx.r9.s64 = -2112356352;
	ctx.r31.u64 = ctx.r3.u64;
	ctx.r30.u64 = ctx.r4.u64;
	ctx.r29.u64 = ctx.r5.u64;
	ctx.r28.u64 = ctx.r6.u64;
	ctx.r27.u64 = ctx.r7.u64;
	ctx.r8.s64 = ctx.r10.s64 + 1880;
	ctx.r7.s64 = 2;
	ctx.r6.s64 = 8;
	ctx.r5.u64 = ctx.r11.u32 & 0xFFFF;
	ctx.r4.s64 = 0;
	ctx.r3.s64 = ctx.r9.s64 + -6824;
	ctx.lr = 0x8217E728;
	sub_82092908(ctx, base);
	ctx.r11.s64 = -2113798144;
	ctx.r24.u64 = ctx.r3.u64;
	ctx.r5.s64 = ctx.r11.s64 + 1836;
	ctx.r6.s64 = 103;
	ctx.r4.s64 = 0;
	ctx.r3.s64 = 2368;
	ctx.lr = 0x8217E744;
	sub_82089F58(ctx, base);
	ctx.r5.s64 = 2368;
	ctx.r4.s64 = 0;
	REX_STORE_U32(ctx.r24.u32 + 48, ctx.r3.u32);
	ctx.r23.u64 = ctx.r3.u64;
	ctx.lr = 0x8217E758;
	sub_822F61C0(ctx, base);
	ctx.r11.u64 = REX_LOAD_U32(ctx.r1.u32 + 244);
	ctx.r10.s64 = 1;
	REX_STORE_U32(ctx.r23.u32 + 0, ctx.r25.u32);
	REX_STORE_U8(ctx.r23.u32 + 9, ctx.r30.u8);
	ctx.r3.u64 = ctx.r24.u64;
	REX_STORE_U8(ctx.r23.u32 + 10, ctx.r10.u8);
	ctx.r4.u64 = ctx.r29.u64;
	REX_STORE_U8(ctx.r23.u32 + 11, ctx.r31.u8);
	REX_STORE_U32(ctx.r23.u32 + 4, ctx.r11.u32);
	REX_STORE_U16(ctx.r23.u32 + 14, ctx.r26.u16);
	REX_STORE_U32(ctx.r23.u32 + 36, ctx.r27.u32);
	ctx.lr = 0x8217E788;
	sub_8217E490(ctx, base);
	ctx.r3.u64 = ctx.r24.u64;
	ctx.r5.u64 = ctx.r28.u64;
	ctx.r4.s64 = 6;
	ctx.lr = 0x8217E798;
	sub_8217E5E8(ctx, base);
	ctx.r3.u64 = ctx.r24.u64;
	ctx.r1.s64 = ctx.r1.s64 + 160;
	__restgprlr_23(ctx, base);
	return;
}
