; ModuleID = 'E:\llvm-test-suite\SingleSource\Benchmarks\Misc\flops-1.c'
source_filename = "E:\\llvm-test-suite\\SingleSource\\Benchmarks\\Misc\\flops-1.c"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-w64-windows-gnu"

@A0 = dso_local global double 1.000000e+00, align 8
@A1 = dso_local global double f0xBFC5555555559705, align 8
@A2 = dso_local global double f0x3F811111113AE9A3, align 8
@A3 = dso_local global double f0x3F2A01A03FB1CA71, align 8
@A4 = dso_local global double f0x3EC71DF284AA3566, align 8
@A5 = dso_local global double f0x3E5AEB5A8CF8A426, align 8
@A6 = dso_local global double f0x3DE68DF75229C1A6, align 8
@B0 = dso_local global double 1.000000e+00, align 8
@B1 = dso_local global double f0xBFDFFFFFFFFF8156, align 8
@B2 = dso_local global double f0x3FA5555555290224, align 8
@B3 = dso_local global double f0xBF56C16BFFE76516, align 8
@B4 = dso_local global double f0x3EFA019528242DB7, align 8
@B5 = dso_local global double f0xBE927BB3D47DDB8E, align 8
@B6 = dso_local global double f0x3E2157B275DF182A, align 8
@C0 = dso_local global double 1.000000e+00, align 8
@C1 = dso_local global double f0x3FEFFFFFFE37B3E2, align 8
@C2 = dso_local global double f0x3FDFFFFFCC2BA4B8, align 8
@C3 = dso_local global double f0x3FC555587C476915, align 8
@C4 = dso_local global double f0x3FA5555B7E795548, align 8
@C5 = dso_local global double f0x3F810D9A4AD9120C, align 8
@C6 = dso_local global double f0x3F5713187EDB8C05, align 8
@C7 = dso_local global double f0x3F26C077C8173F3A, align 8
@C8 = dso_local global double f0x3F049D03FE04B1CF, align 8
@D1 = dso_local global double f0x3FA47AE143138374, align 8
@D2 = dso_local global double 9.600000e-04, align 8
@D3 = dso_local global double f0x3EB4B05A0FF4A728, align 8
@E2 = dso_local global double 4.800000e-04, align 8
@E3 = dso_local global double 4.110510e-07, align 8
@.str = private unnamed_addr constant [2 x i8] c"\0A\00", align 1
@.str.1 = private unnamed_addr constant [58 x i8] c"   FLOPS C Program (Double Precision), V2.0 18 Dec 1992\0A\0A\00", align 1
@T = dso_local global [36 x double] zeroinitializer, align 16
@TLimit = dso_local global double 0.000000e+00, align 8
@piref = dso_local global double 0.000000e+00, align 8
@one = dso_local global double 0.000000e+00, align 8
@two = dso_local global double 0.000000e+00, align 8
@three = dso_local global double 0.000000e+00, align 8
@four = dso_local global double 0.000000e+00, align 8
@five = dso_local global double 0.000000e+00, align 8
@scale = dso_local global double 0.000000e+00, align 8
@.str.2 = private unnamed_addr constant [48 x i8] c"   Module     Error        RunTime      MFLOPS\0A\00", align 1
@.str.3 = private unnamed_addr constant [36 x i8] c"                            (usec)\0A\00", align 1
@sa = dso_local global double 0.000000e+00, align 8
@sb = dso_local global double 0.000000e+00, align 8
@sc = dso_local global double 0.000000e+00, align 8
@.str.4 = private unnamed_addr constant [36 x i8] c"     1   %13.4lf  %10.4lf  %10.4lf\0A\00", align 1
@nulltime = dso_local global double 0.000000e+00, align 8
@TimeArray = dso_local global [3 x double] zeroinitializer, align 16
@sd = dso_local global double 0.000000e+00, align 8
@piprg = dso_local global double 0.000000e+00, align 8
@pierr = dso_local global double 0.000000e+00, align 8

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca double, align 8
  %3 = alloca double, align 8
  %4 = alloca double, align 8
  %5 = alloca double, align 8
  %6 = alloca double, align 8
  %7 = alloca i32, align 4
  %8 = alloca i32, align 4
  %9 = alloca i32, align 4
  %10 = alloca i32, align 4
  %11 = alloca i32, align 4
  store i32 0, ptr %1, align 4
  %12 = call i32 (ptr, ...) @printf(ptr noundef @.str)
  %13 = call i32 (ptr, ...) @printf(ptr noundef @.str.1)
  store i32 15625, ptr %7, align 4
  %14 = load i32, ptr %7, align 4
  %15 = sitofp i32 %14 to double
  %16 = fdiv double 1.000000e+06, %15
  store double %16, ptr getelementptr inbounds nuw (i8, ptr @T, i64 8), align 8
  store double 1.000000e+00, ptr @TLimit, align 8
  store i32 512000000, ptr %8, align 4
  store double f0x400921FB54442D18, ptr @piref, align 8
  store double 1.000000e+00, ptr @one, align 8
  store double 2.000000e+00, ptr @two, align 8
  store double 3.000000e+00, ptr @three, align 8
  store double 4.000000e+00, ptr @four, align 8
  store double 5.000000e+00, ptr @five, align 8
  %17 = load double, ptr @one, align 8
  store double %17, ptr @scale, align 8
  %18 = call i32 (ptr, ...) @printf(ptr noundef @.str.2)
  %19 = call i32 (ptr, ...) @printf(ptr noundef @.str.3)
  %20 = load i32, ptr %7, align 4
  %21 = mul nsw i32 %20, 10000
  store i32 %21, ptr %11, align 4
  store double 0.000000e+00, ptr @sa, align 8
  %22 = load i32, ptr %11, align 4
  %23 = mul nsw i32 2, %22
  store i32 %23, ptr %11, align 4
  %24 = load double, ptr @one, align 8
  %25 = load i32, ptr %11, align 4
  %26 = sitofp i32 %25 to double
  %27 = fdiv double %24, %26
  store double %27, ptr %6, align 8
  store double 0.000000e+00, ptr %2, align 8
  store double 0.000000e+00, ptr %4, align 8
  %28 = load double, ptr @one, align 8
  store double %28, ptr %5, align 8
  store i32 1, ptr %9, align 4
  br label %29

29:                                               ; preds = %61, %0
  %30 = load i32, ptr %9, align 4
  %31 = load i32, ptr %11, align 4
  %32 = sub nsw i32 %31, 1
  %33 = icmp sle i32 %30, %32
  br i1 %33, label %34, label %64

34:                                               ; preds = %29
  %35 = load double, ptr %4, align 8
  %36 = load double, ptr %5, align 8
  %37 = fadd double %35, %36
  store double %37, ptr %4, align 8
  %38 = load double, ptr %4, align 8
  %39 = load double, ptr %6, align 8
  %40 = fmul double %38, %39
  store double %40, ptr %3, align 8
  %41 = load double, ptr %2, align 8
  %42 = load double, ptr @D1, align 8
  %43 = load double, ptr %3, align 8
  %44 = load double, ptr @D2, align 8
  %45 = load double, ptr %3, align 8
  %46 = load double, ptr @D3, align 8
  %47 = call double @llvm.fmuladd.f64(double %45, double %46, double %44)
  %48 = call double @llvm.fmuladd.f64(double %43, double %47, double %42)
  %49 = load double, ptr %5, align 8
  %50 = load double, ptr %3, align 8
  %51 = load double, ptr @D1, align 8
  %52 = load double, ptr %3, align 8
  %53 = load double, ptr @E2, align 8
  %54 = load double, ptr %3, align 8
  %55 = load double, ptr @E3, align 8
  %56 = call double @llvm.fmuladd.f64(double %54, double %55, double %53)
  %57 = call double @llvm.fmuladd.f64(double %52, double %56, double %51)
  %58 = call double @llvm.fmuladd.f64(double %50, double %57, double %49)
  %59 = fdiv double %48, %58
  %60 = fadd double %41, %59
  store double %60, ptr %2, align 8
  br label %61

61:                                               ; preds = %34
  %62 = load i32, ptr %9, align 4
  %63 = add nsw i32 %62, 1
  store i32 %63, ptr %9, align 4
  br label %29, !llvm.loop !7

64:                                               ; preds = %29
  %65 = load double, ptr @D1, align 8
  %66 = load double, ptr @D2, align 8
  %67 = fadd double %65, %66
  %68 = load double, ptr @D3, align 8
  %69 = fadd double %67, %68
  %70 = load double, ptr @one, align 8
  %71 = load double, ptr @D1, align 8
  %72 = fadd double %70, %71
  %73 = load double, ptr @E2, align 8
  %74 = fadd double %72, %73
  %75 = load double, ptr @E3, align 8
  %76 = fadd double %74, %75
  %77 = fdiv double %69, %76
  store double %77, ptr @sa, align 8
  %78 = load double, ptr @D1, align 8
  store double %78, ptr @sb, align 8
  %79 = load double, ptr %6, align 8
  %80 = load double, ptr @sa, align 8
  %81 = load double, ptr @sb, align 8
  %82 = fadd double %80, %81
  %83 = load double, ptr @two, align 8
  %84 = load double, ptr %2, align 8
  %85 = call double @llvm.fmuladd.f64(double %83, double %84, double %82)
  %86 = fmul double %79, %85
  %87 = load double, ptr @two, align 8
  %88 = fdiv double %86, %87
  store double %88, ptr @sa, align 8
  %89 = load double, ptr @one, align 8
  %90 = load double, ptr @sa, align 8
  %91 = fdiv double %89, %90
  store double %91, ptr @sb, align 8
  %92 = load double, ptr @sb, align 8
  %93 = fptosi double %92 to i32
  %94 = mul nsw i32 40000, %93
  %95 = sitofp i32 %94 to double
  %96 = load double, ptr @scale, align 8
  %97 = fdiv double %95, %96
  %98 = fptosi double %97 to i32
  store i32 %98, ptr %11, align 4
  %99 = load double, ptr @sb, align 8
  %100 = fsub double %99, 2.520000e+01
  store double %100, ptr @sc, align 8
  %101 = load double, ptr @sc, align 8
  %102 = fmul double %101, 1.000000e-30
  %103 = call i32 (ptr, ...) @printf(ptr noundef @.str.4, double noundef %102, double noundef 0.000000e+00, double noundef 0.000000e+00)
  ret i32 0
}

declare dso_local i32 @printf(ptr noundef, ...) #1

; Function Attrs: nocallback nocreateundeforpoison nofree nosync nounwind speculatable willreturn memory(none)
declare double @llvm.fmuladd.f64(double, double, double) #2

attributes #0 = { noinline nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #2 = { nocallback nocreateundeforpoison nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5}
!llvm.ident = !{!6}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)", isOptimized: false, runtimeVersion: 0, emissionKind: NoDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "E:\\llvm-test-suite\\SingleSource\\Benchmarks\\Misc/flops-1.c", directory: "E:/project")
!2 = !{i32 2, !"Debug Info Version", i32 3}
!3 = !{i32 8, !"PIC Level", i32 2}
!4 = !{i32 7, !"uwtable", i32 2}
!5 = !{i32 1, !"MaxTLSAlign", i32 65536}
!6 = !{!"clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)"}
!7 = distinct !{!7, !8}
!8 = !{!"llvm.loop.mustprogress"}
