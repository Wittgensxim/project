; ModuleID = 'E:\llvm-test-suite\SingleSource\Benchmarks\Misc\flops-2.c'
source_filename = "E:\\llvm-test-suite\\SingleSource\\Benchmarks\\Misc\\flops-2.c"
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
@sc = dso_local global double 0.000000e+00, align 8
@sb = dso_local global double 0.000000e+00, align 8
@piprg = dso_local global double 0.000000e+00, align 8
@pierr = dso_local global double 0.000000e+00, align 8
@.str.4 = private unnamed_addr constant [36 x i8] c"     2   %13.4lf  %10.4lf  %10.4lf\0A\00", align 1
@nulltime = dso_local global double 0.000000e+00, align 8
@TimeArray = dso_local global [3 x double] zeroinitializer, align 16
@T = dso_local global [36 x double] zeroinitializer, align 16
@sd = dso_local global double 0.000000e+00, align 8

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
  store double 1.000000e+00, ptr @TLimit, align 8
  store i32 512000000, ptr %8, align 4
  store double f0x400921FB54442D18, ptr @piref, align 8
  store double 1.000000e+00, ptr @one, align 8
  store double 2.000000e+00, ptr @two, align 8
  store double 3.000000e+00, ptr @three, align 8
  store double 4.000000e+00, ptr @four, align 8
  store double 5.000000e+00, ptr @five, align 8
  %14 = load double, ptr @one, align 8
  store double %14, ptr @scale, align 8
  %15 = call i32 (ptr, ...) @printf(ptr noundef @.str.2)
  %16 = call i32 (ptr, ...) @printf(ptr noundef @.str.3)
  %17 = load i32, ptr %7, align 4
  %18 = mul nsw i32 %17, 10000
  store i32 %18, ptr %10, align 4
  %19 = load double, ptr @five, align 8
  %20 = fneg double %19
  store double %20, ptr %2, align 8
  %21 = load double, ptr @one, align 8
  %22 = fneg double %21
  store double %22, ptr @sa, align 8
  store i32 1, ptr %9, align 4
  br label %23

23:                                               ; preds = %33, %0
  %24 = load i32, ptr %9, align 4
  %25 = load i32, ptr %10, align 4
  %26 = icmp sle i32 %24, %25
  br i1 %26, label %27, label %36

27:                                               ; preds = %23
  %28 = load double, ptr %2, align 8
  %29 = fneg double %28
  store double %29, ptr %2, align 8
  %30 = load double, ptr @sa, align 8
  %31 = load double, ptr %2, align 8
  %32 = fadd double %30, %31
  store double %32, ptr @sa, align 8
  br label %33

33:                                               ; preds = %27
  %34 = load i32, ptr %9, align 4
  %35 = add nsw i32 %34, 1
  store i32 %35, ptr %9, align 4
  br label %23, !llvm.loop !7

36:                                               ; preds = %23
  %37 = load i32, ptr %10, align 4
  %38 = sitofp i32 %37 to double
  store double %38, ptr @sc, align 8
  %39 = load double, ptr @sa, align 8
  store double %39, ptr %3, align 8
  store double 0.000000e+00, ptr %4, align 8
  store double 0.000000e+00, ptr %5, align 8
  store double 0.000000e+00, ptr %6, align 8
  store i32 1, ptr %9, align 4
  br label %40

40:                                               ; preds = %68, %36
  %41 = load i32, ptr %9, align 4
  %42 = load i32, ptr %10, align 4
  %43 = icmp sle i32 %41, %42
  br i1 %43, label %44, label %71

44:                                               ; preds = %40
  %45 = load double, ptr %2, align 8
  %46 = fneg double %45
  store double %46, ptr %2, align 8
  %47 = load double, ptr @sa, align 8
  %48 = load double, ptr %2, align 8
  %49 = fadd double %47, %48
  store double %49, ptr @sa, align 8
  %50 = load double, ptr %3, align 8
  %51 = load double, ptr @two, align 8
  %52 = fadd double %50, %51
  store double %52, ptr %3, align 8
  %53 = load double, ptr %6, align 8
  %54 = load double, ptr %2, align 8
  %55 = load double, ptr %3, align 8
  %56 = fsub double %54, %55
  %57 = fadd double %53, %56
  store double %57, ptr %6, align 8
  %58 = load double, ptr %4, align 8
  %59 = load double, ptr %2, align 8
  %60 = load double, ptr %3, align 8
  %61 = fneg double %59
  %62 = call double @llvm.fmuladd.f64(double %61, double %60, double %58)
  store double %62, ptr %4, align 8
  %63 = load double, ptr %5, align 8
  %64 = load double, ptr %2, align 8
  %65 = load double, ptr %3, align 8
  %66 = fdiv double %64, %65
  %67 = fadd double %63, %66
  store double %67, ptr %5, align 8
  br label %68

68:                                               ; preds = %44
  %69 = load i32, ptr %9, align 4
  %70 = add nsw i32 %69, 1
  store i32 %70, ptr %9, align 4
  br label %40, !llvm.loop !9

71:                                               ; preds = %40
  %72 = load double, ptr @sa, align 8
  %73 = load double, ptr %6, align 8
  %74 = fmul double %72, %73
  %75 = load double, ptr @sc, align 8
  %76 = fdiv double %74, %75
  %77 = fptosi double %76 to i32
  store i32 %77, ptr %10, align 4
  %78 = load double, ptr @four, align 8
  %79 = load double, ptr %5, align 8
  %80 = fmul double %78, %79
  %81 = load double, ptr @five, align 8
  %82 = fdiv double %80, %81
  store double %82, ptr @sa, align 8
  %83 = load double, ptr @sa, align 8
  %84 = load double, ptr @five, align 8
  %85 = load double, ptr %4, align 8
  %86 = fdiv double %84, %85
  %87 = fadd double %83, %86
  store double %87, ptr @sb, align 8
  store double 3.125000e+01, ptr @sc, align 8
  %88 = load double, ptr @sb, align 8
  %89 = load double, ptr @sc, align 8
  %90 = load double, ptr %4, align 8
  %91 = load double, ptr %4, align 8
  %92 = fmul double %90, %91
  %93 = load double, ptr %4, align 8
  %94 = fmul double %92, %93
  %95 = fdiv double %89, %94
  %96 = fsub double %88, %95
  store double %96, ptr @piprg, align 8
  %97 = load double, ptr @piprg, align 8
  %98 = load double, ptr @piref, align 8
  %99 = fsub double %97, %98
  store double %99, ptr @pierr, align 8
  %100 = load double, ptr @pierr, align 8
  %101 = fmul double %100, 1.000000e-30
  %102 = call i32 (ptr, ...) @printf(ptr noundef @.str.4, double noundef %101, double noundef 0.000000e+00, double noundef 0.000000e+00)
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
!1 = !DIFile(filename: "E:\\llvm-test-suite\\SingleSource\\Benchmarks\\Misc/flops-2.c", directory: "E:/project")
!2 = !{i32 2, !"Debug Info Version", i32 3}
!3 = !{i32 8, !"PIC Level", i32 2}
!4 = !{i32 7, !"uwtable", i32 2}
!5 = !{i32 1, !"MaxTLSAlign", i32 65536}
!6 = !{!"clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)"}
!7 = distinct !{!7, !8}
!8 = !{!"llvm.loop.mustprogress"}
!9 = distinct !{!9, !8}
