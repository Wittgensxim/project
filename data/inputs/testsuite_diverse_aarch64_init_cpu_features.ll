; ModuleID = 'E:\llvm-test-suite\SingleSource\Benchmarks\Misc\aarch64-init-cpu-features.c'
source_filename = "E:\\llvm-test-suite\\SingleSource\\Benchmarks\\Misc\\aarch64-init-cpu-features.c"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-w64-windows-gnu"

%struct.anon = type { i64 }

@__aarch64_cpu_features = external global %struct.anon, align 8
@.str = private unnamed_addr constant [43 x i8] c"FAILED consistency test: 0x%llx != 0x%llx\0A\00", align 1

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i64, align 8
  %3 = alloca i32, align 4
  store i32 0, ptr %1, align 4
  call void @RUNTIME_INIT()
  %4 = load i64, ptr @__aarch64_cpu_features, align 8
  store i64 %4, ptr %2, align 8
  store i64 0, ptr @__aarch64_cpu_features, align 8
  call void @RUNTIME_INIT()
  %5 = load i64, ptr @__aarch64_cpu_features, align 8
  %6 = load i64, ptr %2, align 8
  %7 = icmp ne i64 %5, %6
  br i1 %7, label %8, label %12

8:                                                ; preds = %0
  %9 = load i64, ptr %2, align 8
  %10 = load i64, ptr @__aarch64_cpu_features, align 8
  %11 = call i32 (ptr, ...) @printf(ptr noundef @.str, i64 noundef %9, i64 noundef %10)
  store i32 1, ptr %1, align 4
  br label %20

12:                                               ; preds = %0
  store i32 0, ptr %3, align 4
  br label %13

13:                                               ; preds = %17, %12
  %14 = load i32, ptr %3, align 4
  %15 = icmp slt i32 %14, 1000000
  br i1 %15, label %16, label %20

16:                                               ; preds = %13
  store i64 0, ptr @__aarch64_cpu_features, align 8
  call void @RUNTIME_INIT()
  br label %17

17:                                               ; preds = %16
  %18 = load i32, ptr %3, align 4
  %19 = add nsw i32 %18, 1
  store i32 %19, ptr %3, align 4
  br label %13, !llvm.loop !7

20:                                               ; preds = %8, %13
  %21 = load i32, ptr %1, align 4
  ret i32 %21
}

declare dso_local void @RUNTIME_INIT() #1

declare dso_local i32 @printf(ptr noundef, ...) #1

attributes #0 = { noinline nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5}
!llvm.ident = !{!6}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)", isOptimized: false, runtimeVersion: 0, emissionKind: NoDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "E:\\llvm-test-suite\\SingleSource\\Benchmarks\\Misc/aarch64-init-cpu-features.c", directory: "E:/project")
!2 = !{i32 2, !"Debug Info Version", i32 3}
!3 = !{i32 8, !"PIC Level", i32 2}
!4 = !{i32 7, !"uwtable", i32 2}
!5 = !{i32 1, !"MaxTLSAlign", i32 65536}
!6 = !{!"clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)"}
!7 = distinct !{!7, !8}
!8 = !{!"llvm.loop.mustprogress"}
