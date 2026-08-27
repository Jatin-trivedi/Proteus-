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

define i8* @"struct_test"()
{
entry:
  %"p" = alloca i8*
  br label %"main"
main:
  store i8* null, i8** %"p"
  %".3" = bitcast [5 x i8]* @".str_1" to i8*
  ret i8* %".3"
}

@".str_1" = internal constant [5 x i8] c"John\00"