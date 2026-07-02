; ModuleID = 'E:\llvm-test-suite\SingleSource\UnitTests\2002-05-02-ArgumentTest.c'
source_filename = "E:\\llvm-test-suite\\SingleSource\\UnitTests\\2002-05-02-ArgumentTest.c"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-w64-windows-gnu"

@.str = private unnamed_addr constant [26 x i8] c"%d, %f, %d, %lld, %d, %f\0A\00", align 1

; Function Attrs: noinline nounwind uwtable
define dso_local void @testfunc(i16 noundef %0, float noundef %1, i8 noundef %2, i64 noundef %3, i32 noundef %4, double noundef %5) #0 {
  %7 = alloca i16, align 2
  %8 = alloca float, align 4
  %9 = alloca i8, align 1
  %10 = alloca i64, align 8
  %11 = alloca i32, align 4
  %12 = alloca double, align 8
  store i16 %0, ptr %7, align 2
  store float %1, ptr %8, align 4
  store i8 %2, ptr %9, align 1
  store i64 %3, ptr %10, align 8
  store i32 %4, ptr %11, align 4
  store double %5, ptr %12, align 8
  %13 = load i16, ptr %7, align 2
  %14 = sext i16 %13 to i32
  %15 = load float, ptr %8, align 4
  %16 = fpext float %15 to double
  %17 = load i8, ptr %9, align 1
  %18 = sext i8 %17 to i32
  %19 = load i64, ptr %10, align 8
  %20 = load i32, ptr %11, align 4
  %21 = load double, ptr %12, align 8
  %22 = call i32 (ptr, ...) @printf(ptr noundef @.str, i32 noundef %14, double noundef %16, i32 noundef %18, i64 noundef %19, i32 noundef %20, double noundef %21)
  ret void
}

declare dso_local i32 @printf(ptr noundef, ...) #1

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @main() #0 {
  %1 = alloca i32, align 4
  store i32 0, ptr %1, align 4
  call void @testfunc(i16 noundef 12, float noundef 1.245000e+00, i8 noundef 120, i64 noundef 123456677890, i32 noundef -10, double noundef 4.500000e+15)
  ret i32 0
}

attributes #0 = { noinline nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5}
!llvm.ident = !{!6}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)", isOptimized: false, runtimeVersion: 0, emissionKind: NoDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "E:\\llvm-test-suite\\SingleSource\\UnitTests/2002-05-02-ArgumentTest.c", directory: "E:/project")
!2 = !{i32 2, !"Debug Info Version", i32 3}
!3 = !{i32 8, !"PIC Level", i32 2}
!4 = !{i32 7, !"uwtable", i32 2}
!5 = !{i32 1, !"MaxTLSAlign", i32 65536}
!6 = !{!"clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)"}
