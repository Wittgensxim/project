; ModuleID = 'E:\llvm-test-suite\SingleSource\Regression\C\2003-05-21-BitfieldHandling.c'
source_filename = "E:\\llvm-test-suite\\SingleSource\\Regression\\C\\2003-05-21-BitfieldHandling.c"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-w64-windows-gnu"

%struct.test1 = type { i8, [7 x i8] }
%struct.test2 = type { i64 }
%struct.test3 = type { i8, i64 }
%struct.test4 = type { i8, i64, i16 }
%struct.test5 = type { i8, i64, i8 }
%struct.test6 = type { i8, i64, i32 }
%struct.test = type { i8, i8, [2 x i8], i8, i64 }
%struct.test_empty = type {}

@Esize = dso_local global i32 0, align 4
@N = dso_local global { i16, [14 x i8], i8, [7 x i8], i8, i8, i8, i8, i8, i8, i8, i8 } { i16 2, [14 x i8] zeroinitializer, i8 7, [7 x i8] zeroinitializer, i8 1, i8 0, i8 0, i8 0, i8 0, i8 0, i8 0, i8 0 }, align 8
@Nsize = dso_local global i32 32, align 4
@F1size = dso_local global i32 8, align 4
@F2size = dso_local global i32 8, align 4
@F3size = dso_local global i32 16, align 4
@F4size = dso_local global i32 24, align 4
@F5size = dso_local global i32 24, align 4
@F6size = dso_local global i32 24, align 4
@Msize = dso_local global i32 16, align 4
@.str = private unnamed_addr constant [16 x i8] c"N: %d %d %d %d\0A\00", align 1
@.str.1 = private unnamed_addr constant [8 x i8] c"F1: %d\0A\00", align 1
@F1 = dso_local global %struct.test1 zeroinitializer, align 8
@.str.2 = private unnamed_addr constant [8 x i8] c"F2: %d\0A\00", align 1
@F2 = dso_local global %struct.test2 zeroinitializer, align 8
@.str.3 = private unnamed_addr constant [8 x i8] c"F3: %d\0A\00", align 1
@F3 = dso_local global %struct.test3 zeroinitializer, align 8
@.str.4 = private unnamed_addr constant [11 x i8] c"F4: %d %d\0A\00", align 1
@F4 = dso_local global %struct.test4 zeroinitializer, align 8
@.str.5 = private unnamed_addr constant [11 x i8] c"F5: %d %d\0A\00", align 1
@F5 = dso_local global %struct.test5 zeroinitializer, align 8
@.str.6 = private unnamed_addr constant [11 x i8] c"F6: %d %d\0A\00", align 1
@F6 = dso_local global %struct.test6 zeroinitializer, align 8
@.str.7 = private unnamed_addr constant [19 x i8] c"M: %d %d %d %d %d\0A\00", align 1
@M = dso_local global %struct.test zeroinitializer, align 8
@e = dso_local global %struct.test_empty zeroinitializer, align 1

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @main() #0 {
  %1 = alloca i32, align 4
  store i32 0, ptr %1, align 4
  %2 = load i16, ptr @N, align 8
  %3 = zext i16 %2 to i32
  %4 = load i32, ptr getelementptr inbounds nuw (i8, ptr @N, i64 16), align 8
  %5 = shl i32 %4, 24
  %6 = ashr i32 %5, 24
  %7 = load i64, ptr getelementptr inbounds nuw (i8, ptr @N, i64 24), align 8
  %8 = shl i64 %7, 33
  %9 = ashr i64 %8, 33
  %10 = trunc i64 %9 to i32
  %11 = load i64, ptr getelementptr inbounds nuw (i8, ptr @N, i64 24), align 8
  %12 = shl i64 %11, 2
  %13 = ashr i64 %12, 33
  %14 = trunc i64 %13 to i32
  %15 = call i32 (ptr, ...) @printf(ptr noundef @.str, i32 noundef %3, i32 noundef %6, i32 noundef %10, i32 noundef %14)
  %16 = load i8, ptr @F1, align 8
  %17 = shl i8 %16, 7
  %18 = ashr i8 %17, 7
  %19 = sext i8 %18 to i32
  %20 = call i32 (ptr, ...) @printf(ptr noundef @.str.1, i32 noundef %19)
  %21 = load i64, ptr @F2, align 8
  %22 = shl i64 %21, 60
  %23 = ashr i64 %22, 60
  %24 = trunc i64 %23 to i32
  %25 = call i32 (ptr, ...) @printf(ptr noundef @.str.2, i32 noundef %24)
  %26 = load i8, ptr @F3, align 8
  %27 = shl i8 %26, 7
  %28 = ashr i8 %27, 7
  %29 = sext i8 %28 to i32
  %30 = call i32 (ptr, ...) @printf(ptr noundef @.str.3, i32 noundef %29)
  %31 = load i8, ptr @F4, align 8
  %32 = shl i8 %31, 7
  %33 = ashr i8 %32, 7
  %34 = sext i8 %33 to i32
  %35 = load i16, ptr getelementptr inbounds nuw (i8, ptr @F4, i64 16), align 8
  %36 = shl i16 %35, 2
  %37 = ashr i16 %36, 2
  %38 = sext i16 %37 to i32
  %39 = call i32 (ptr, ...) @printf(ptr noundef @.str.4, i32 noundef %34, i32 noundef %38)
  %40 = load i8, ptr @F5, align 8
  %41 = shl i8 %40, 7
  %42 = ashr i8 %41, 7
  %43 = sext i8 %42 to i32
  %44 = load i8, ptr getelementptr inbounds nuw (i8, ptr @F5, i64 16), align 8
  %45 = shl i8 %44, 7
  %46 = ashr i8 %45, 7
  %47 = sext i8 %46 to i32
  %48 = call i32 (ptr, ...) @printf(ptr noundef @.str.5, i32 noundef %43, i32 noundef %47)
  %49 = load i8, ptr @F6, align 8
  %50 = shl i8 %49, 7
  %51 = ashr i8 %50, 7
  %52 = sext i8 %51 to i32
  %53 = load i32, ptr getelementptr inbounds nuw (i8, ptr @F6, i64 16), align 8
  %54 = shl i32 %53, 11
  %55 = ashr i32 %54, 11
  %56 = call i32 (ptr, ...) @printf(ptr noundef @.str.6, i32 noundef %52, i32 noundef %55)
  %57 = load i8, ptr @M, align 8
  %58 = sext i8 %57 to i32
  %59 = load i8, ptr getelementptr inbounds nuw (i8, ptr @M, i64 1), align 1
  %60 = shl i8 %59, 5
  %61 = ashr i8 %60, 5
  %62 = sext i8 %61 to i32
  %63 = load i8, ptr getelementptr inbounds nuw (i8, ptr @M, i64 1), align 1
  %64 = shl i8 %63, 2
  %65 = ashr i8 %64, 5
  %66 = sext i8 %65 to i32
  %67 = load i8, ptr getelementptr inbounds nuw (i8, ptr @M, i64 4), align 4
  %68 = sext i8 %67 to i32
  %69 = load i64, ptr getelementptr inbounds nuw (i8, ptr @M, i64 8), align 8
  %70 = shl i64 %69, 60
  %71 = ashr i64 %70, 60
  %72 = trunc i64 %71 to i32
  %73 = call i32 (ptr, ...) @printf(ptr noundef @.str.7, i32 noundef %58, i32 noundef %62, i32 noundef %66, i32 noundef %68, i32 noundef %72)
  ret i32 0
}

declare dso_local i32 @printf(ptr noundef, ...) #1

attributes #0 = { noinline nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5}
!llvm.ident = !{!6}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)", isOptimized: false, runtimeVersion: 0, emissionKind: NoDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "E:\\llvm-test-suite\\SingleSource\\Regression\\C/2003-05-21-BitfieldHandling.c", directory: "E:/project")
!2 = !{i32 2, !"Debug Info Version", i32 3}
!3 = !{i32 8, !"PIC Level", i32 2}
!4 = !{i32 7, !"uwtable", i32 2}
!5 = !{i32 1, !"MaxTLSAlign", i32 65536}
!6 = !{!"clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)"}
