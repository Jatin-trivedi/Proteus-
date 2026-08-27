; ModuleID = "jocky_module"
target triple = "x86_64-pc-windows-gnu"
target datalayout = ""

declare i8* @"jocky_collect_registry"(i8* %".1")

declare i8* @"jocky_get_processes"()

declare i8* @"jocky_get_system_info"()

declare i8* @"jocky_scan_network"()

declare i32 @"printf"(i8* %".1", ...)

declare i32 @"puts"(i8* %".1")

declare i8* @"jocky_int_to_str"(i64 %".1")

define i8* @"array_test"()
{
entry:
  %"arr" = alloca i64
  %"first" = alloca i64
  br label %"main"
main:
  store i64 10, i64* %"arr"
  %".3" = load i64, i64* %"arr"
  store i64 %".3", i64* %"first"
  %".5" = load i64, i64* %"first"
  %".7" = call i8* @"jocky_int_to_str"(i64 %".5")
  ret i8* %".7"
}
