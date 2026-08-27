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

define i8* @"while_test"()
{
entry:
  %"i" = alloca i64
  %"sum" = alloca i64
  br label %"main"
main:
  store i64 0, i64* %"i"
  store i64 0, i64* %"sum"
  br label %"while_header_1"
while_header_1:
  %".5" = load i64, i64* %"i"
  %".6" = icmp slt i64 %".5", 5
  br i1 %".6", label %"while_body_1", label %"while_end_1"
while_body_1:
  %".8" = load i64, i64* %"sum"
  %".9" = load i64, i64* %"i"
  %".10" = add i64 %".8", %".9"
  store i64 %".10", i64* %"sum"
  %".12" = load i64, i64* %"i"
  %".13" = add i64 %".12", 1
  store i64 %".13", i64* %"i"
  br label %"while_header_1"
while_end_1:
  %".16" = load i64, i64* %"sum"
  %".18" = call i8* @"jocky_int_to_str"(i64 %".16")
  ret i8* %".18"
}
