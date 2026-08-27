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

define i8* @"for_test"()
{
entry:
  %"sum" = alloca i64
  %"for_counter" = alloca i64
  br label %"main"
main:
  store i64 0, i64* %"sum"
  store i64 0, i64* %"for_counter"
  br label %"for_header_1"
for_header_1:
  %".5" = load i64, i64* %"for_counter"
  %".6" = icmp slt i64 %".5", 5
  br i1 %".6", label %"for_body_1", label %"for_end_1"
for_body_1:
  %".8" = load i64, i64* %"sum"
  %".9" = load i64, i64* %"for_counter"
  %".10" = add i64 %".8", %".9"
  store i64 %".10", i64* %"sum"
  %".12" = add i64 %".5", 1
  store i64 %".12", i64* %"for_counter"
  br label %"for_header_1"
for_end_1:
  %".15" = load i64, i64* %"sum"
  %".17" = call i8* @"jocky_int_to_str"(i64 %".15")
  ret i8* %".17"
}
