; ModuleID = 'benchmarks\micro\alloca.c'
source_filename = "benchmarks\\micro\\alloca.c"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-w64-windows-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @alloca_sroa(i32 noundef %0) #0 {
  %2 = alloca i32, align 4
  %3 = alloca [2 x i32], align 4
  store i32 %0, ptr %2, align 4
  %4 = load i32, ptr %2, align 4
  %5 = getelementptr inbounds [2 x i32], ptr %3, i64 0, i64 0
  store i32 %4, ptr %5, align 4
  %6 = load i32, ptr %2, align 4
  %7 = add nsw i32 %6, 1
  %8 = getelementptr inbounds [2 x i32], ptr %3, i64 0, i64 1
  store i32 %7, ptr %8, align 4
  %9 = getelementptr inbounds [2 x i32], ptr %3, i64 0, i64 0
  %10 = load i32, ptr %9, align 4
  %11 = getelementptr inbounds [2 x i32], ptr %3, i64 0, i64 1
  %12 = load i32, ptr %11, align 4
  %13 = add nsw i32 %10, %12
  ret i32 %13
}

attributes #0 = { noinline nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5}
!llvm.ident = !{!6}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)", isOptimized: false, runtimeVersion: 0, emissionKind: NoDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "benchmarks\\micro/alloca.c", directory: "E:/project")
!2 = !{i32 2, !"Debug Info Version", i32 3}
!3 = !{i32 8, !"PIC Level", i32 2}
!4 = !{i32 7, !"uwtable", i32 2}
!5 = !{i32 1, !"MaxTLSAlign", i32 65536}
!6 = !{!"clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)"}
