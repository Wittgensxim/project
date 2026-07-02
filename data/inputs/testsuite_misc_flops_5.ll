; ModuleID = 'E:\llvm-test-suite\SingleSource\Benchmarks\Misc\flops-5.c'
source_filename = "E:\\llvm-test-suite\\SingleSource\\Benchmarks\\Misc\\flops-5.c"
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
@sb = dso_local global double 0.000000e+00, align 8
@sc = dso_local global double 0.000000e+00, align 8
@.str.4 = private unnamed_addr constant [36 x i8] c"     5   %13.4lf  %10.4lf  %10.4lf\0A\00", align 1
@nulltime = dso_local global double 0.000000e+00, align 8
@TimeArray = dso_local global [3 x double] zeroinitializer, align 16
@T = dso_local global [36 x double] zeroinitializer, align 16
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
  %19 = load double, ptr @piref, align 8
  %20 = load double, ptr @three, align 8
  %21 = load i32, ptr %10, align 4
  %22 = sitofp i32 %21 to double
  %23 = fmul double %20, %22
  %24 = fdiv double %19, %23
  store double %24, ptr %6, align 8
  store double 0.000000e+00, ptr %2, align 8
  store double 0.000000e+00, ptr %4, align 8
  store i32 1, ptr %9, align 4
  br label %25

25:                                               ; preds = %82, %0
  %26 = load i32, ptr %9, align 4
  %27 = load i32, ptr %10, align 4
  %28 = sub nsw i32 %27, 1
  %29 = icmp sle i32 %26, %28
  br i1 %29, label %30, label %85

30:                                               ; preds = %25
  %31 = load i32, ptr %9, align 4
  %32 = sitofp i32 %31 to double
  %33 = load double, ptr %6, align 8
  %34 = fmul double %32, %33
  store double %34, ptr %3, align 8
  %35 = load double, ptr %3, align 8
  %36 = load double, ptr %3, align 8
  %37 = fmul double %35, %36
  store double %37, ptr %5, align 8
  %38 = load double, ptr %3, align 8
  %39 = load double, ptr @A6, align 8
  %40 = load double, ptr %5, align 8
  %41 = load double, ptr @A5, align 8
  %42 = call double @llvm.fmuladd.f64(double %39, double %40, double %41)
  %43 = load double, ptr %5, align 8
  %44 = load double, ptr @A4, align 8
  %45 = call double @llvm.fmuladd.f64(double %42, double %43, double %44)
  %46 = load double, ptr %5, align 8
  %47 = load double, ptr @A3, align 8
  %48 = call double @llvm.fmuladd.f64(double %45, double %46, double %47)
  %49 = load double, ptr %5, align 8
  %50 = load double, ptr @A2, align 8
  %51 = call double @llvm.fmuladd.f64(double %48, double %49, double %50)
  %52 = load double, ptr %5, align 8
  %53 = load double, ptr @A1, align 8
  %54 = call double @llvm.fmuladd.f64(double %51, double %52, double %53)
  %55 = load double, ptr %5, align 8
  %56 = load double, ptr @one, align 8
  %57 = call double @llvm.fmuladd.f64(double %54, double %55, double %56)
  %58 = fmul double %38, %57
  store double %58, ptr %4, align 8
  %59 = load double, ptr %2, align 8
  %60 = load double, ptr %4, align 8
  %61 = load double, ptr %5, align 8
  %62 = load double, ptr %5, align 8
  %63 = load double, ptr %5, align 8
  %64 = load double, ptr %5, align 8
  %65 = load double, ptr %5, align 8
  %66 = load double, ptr @B6, align 8
  %67 = load double, ptr %5, align 8
  %68 = load double, ptr @B5, align 8
  %69 = call double @llvm.fmuladd.f64(double %66, double %67, double %68)
  %70 = load double, ptr @B4, align 8
  %71 = call double @llvm.fmuladd.f64(double %65, double %69, double %70)
  %72 = load double, ptr @B3, align 8
  %73 = call double @llvm.fmuladd.f64(double %64, double %71, double %72)
  %74 = load double, ptr @B2, align 8
  %75 = call double @llvm.fmuladd.f64(double %63, double %73, double %74)
  %76 = load double, ptr @B1, align 8
  %77 = call double @llvm.fmuladd.f64(double %62, double %75, double %76)
  %78 = load double, ptr @one, align 8
  %79 = call double @llvm.fmuladd.f64(double %61, double %77, double %78)
  %80 = fdiv double %60, %79
  %81 = fadd double %59, %80
  store double %81, ptr %2, align 8
  br label %82

82:                                               ; preds = %30
  %83 = load i32, ptr %9, align 4
  %84 = add nsw i32 %83, 1
  store i32 %84, ptr %9, align 4
  br label %25, !llvm.loop !7

85:                                               ; preds = %25
  %86 = load double, ptr @piref, align 8
  %87 = load double, ptr @three, align 8
  %88 = fdiv double %86, %87
  store double %88, ptr %3, align 8
  %89 = load double, ptr %3, align 8
  %90 = load double, ptr %3, align 8
  %91 = fmul double %89, %90
  store double %91, ptr %5, align 8
  %92 = load double, ptr %3, align 8
  %93 = load double, ptr @A6, align 8
  %94 = load double, ptr %5, align 8
  %95 = load double, ptr @A5, align 8
  %96 = call double @llvm.fmuladd.f64(double %93, double %94, double %95)
  %97 = load double, ptr %5, align 8
  %98 = load double, ptr @A4, align 8
  %99 = call double @llvm.fmuladd.f64(double %96, double %97, double %98)
  %100 = load double, ptr %5, align 8
  %101 = load double, ptr @A3, align 8
  %102 = call double @llvm.fmuladd.f64(double %99, double %100, double %101)
  %103 = load double, ptr %5, align 8
  %104 = load double, ptr @A2, align 8
  %105 = call double @llvm.fmuladd.f64(double %102, double %103, double %104)
  %106 = load double, ptr %5, align 8
  %107 = load double, ptr @A1, align 8
  %108 = call double @llvm.fmuladd.f64(double %105, double %106, double %107)
  %109 = load double, ptr %5, align 8
  %110 = load double, ptr @one, align 8
  %111 = call double @llvm.fmuladd.f64(double %108, double %109, double %110)
  %112 = fmul double %92, %111
  store double %112, ptr @sa, align 8
  %113 = load double, ptr %5, align 8
  %114 = load double, ptr %5, align 8
  %115 = load double, ptr %5, align 8
  %116 = load double, ptr %5, align 8
  %117 = load double, ptr %5, align 8
  %118 = load double, ptr @B6, align 8
  %119 = load double, ptr %5, align 8
  %120 = load double, ptr @B5, align 8
  %121 = call double @llvm.fmuladd.f64(double %118, double %119, double %120)
  %122 = load double, ptr @B4, align 8
  %123 = call double @llvm.fmuladd.f64(double %117, double %121, double %122)
  %124 = load double, ptr @B3, align 8
  %125 = call double @llvm.fmuladd.f64(double %116, double %123, double %124)
  %126 = load double, ptr @B2, align 8
  %127 = call double @llvm.fmuladd.f64(double %115, double %125, double %126)
  %128 = load double, ptr @B1, align 8
  %129 = call double @llvm.fmuladd.f64(double %114, double %127, double %128)
  %130 = load double, ptr @one, align 8
  %131 = call double @llvm.fmuladd.f64(double %113, double %129, double %130)
  store double %131, ptr @sb, align 8
  %132 = load double, ptr @sa, align 8
  %133 = load double, ptr @sb, align 8
  %134 = fdiv double %132, %133
  store double %134, ptr @sa, align 8
  %135 = load double, ptr %6, align 8
  %136 = load double, ptr @sa, align 8
  %137 = load double, ptr @two, align 8
  %138 = load double, ptr %2, align 8
  %139 = call double @llvm.fmuladd.f64(double %137, double %138, double %136)
  %140 = fmul double %135, %139
  %141 = load double, ptr @two, align 8
  %142 = fdiv double %140, %141
  store double %142, ptr @sa, align 8
  store double f0x3FE62E42FEFA39EF, ptr @sb, align 8
  %143 = load double, ptr @sa, align 8
  %144 = load double, ptr @sb, align 8
  %145 = fsub double %143, %144
  store double %145, ptr @sc, align 8
  %146 = load double, ptr @sc, align 8
  %147 = fmul double %146, 1.000000e-30
  %148 = call i32 (ptr, ...) @printf(ptr noundef @.str.4, double noundef %147, double noundef 0.000000e+00, double noundef 0.000000e+00)
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
!1 = !DIFile(filename: "E:\\llvm-test-suite\\SingleSource\\Benchmarks\\Misc/flops-5.c", directory: "E:/project")
!2 = !{i32 2, !"Debug Info Version", i32 3}
!3 = !{i32 8, !"PIC Level", i32 2}
!4 = !{i32 7, !"uwtable", i32 2}
!5 = !{i32 1, !"MaxTLSAlign", i32 65536}
!6 = !{!"clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)"}
!7 = distinct !{!7, !8}
!8 = !{!"llvm.loop.mustprogress"}
