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

define i8* @"if_test"()
{
entry:
  %"x" = alloca i64
  br label %"main"
main:
  store i64 10, i64* %"x"
  %".3" = load i64, i64* %"x"
  %".4" = icmp sgt i64 %".3", 5
  br i1 %".4", label %"if_then_1", label %"if_else_1"
if_then_1:
  %".6" = bitcast [20 x i8]* @".str_1" to i8*
  ret i8* %".6"
if_else_1:
  %".8" = bitcast [24 x i8]* @".str_2" to i8*
  ret i8* %".8"
if_end_1:
  ret i8* null
}

@".str_1" = internal constant [20 x i8] c"x is greater than 5\00"
@".str_2" = internal constant [24 x i8] c"x is not greater than 5\00"