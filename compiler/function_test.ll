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

define i8* @"add"(i64 %".1", i64 %".2")
{
entry:
  %"a" = alloca i64
  %"b" = alloca i64
  br label %"main"
main:
  store i64 %".1", i64* %"a"
  store i64 %".2", i64* %"b"
  %".6" = load i64, i64* %"a"
  %".7" = load i64, i64* %"b"
  %".8" = add i64 %".6", %".7"
  %".10" = call i8* @"jocky_int_to_str"(i64 %".8")
  ret i8* %".10"
}

define i8* @"func_test"()
{
entry:
  %"result" = alloca i8*
  br label %"main"
main:
  %".2" = call i8* @"add"(i64 10, i64 20)
  store i8* %".2", i8** %"result"
  %".4" = load i8*, i8** %"result"
  ret i8* %".4"
}
