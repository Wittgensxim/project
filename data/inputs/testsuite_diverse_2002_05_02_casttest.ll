; ModuleID = 'E:\llvm-test-suite\SingleSource\UnitTests\2002-05-02-CastTest.c'
source_filename = "E:\\llvm-test-suite\\SingleSource\\UnitTests\\2002-05-02-CastTest.c"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-w64-windows-gnu"

@.str = private unnamed_addr constant [23 x i8] c"ubc0 = '%c'\09   [0x%x]\0A\00", align 1
@.str.1 = private unnamed_addr constant [21 x i8] c"ubs0 = %u\09   [0x%x]\0A\00", align 1
@.str.2 = private unnamed_addr constant [21 x i8] c"ubs1 = %u\09   [0x%x]\0A\00", align 1
@.str.3 = private unnamed_addr constant [21 x i8] c"bs0  = %d\09   [0x%x]\0A\00", align 1
@.str.4 = private unnamed_addr constant [21 x i8] c"bs1  = %d\09   [0x%x]\0A\00", align 1
@.str.5 = private unnamed_addr constant [23 x i8] c"c1   = '%c'\09   [0x%x]\0A\00", align 1
@.str.6 = private unnamed_addr constant [21 x i8] c"s1   = %d\09   [0x%x]\0A\00", align 1
@.str.7 = private unnamed_addr constant [23 x i8] c"uc2  = '%c'\09   [0x%x]\0A\00", align 1
@.str.8 = private unnamed_addr constant [21 x i8] c"us2  = %u\09   [0x%x]\0A\00", align 1
@.str.9 = private unnamed_addr constant [23 x i8] c"ic3  = '%c'\09   [0x%x]\0A\00", align 1
@.str.10 = private unnamed_addr constant [21 x i8] c"is3  = %d\09   [0x%x]\0A\00", align 1
@.str.11 = private unnamed_addr constant [21 x i8] c"is4  = %d\09   [0x%x]\0A\00", align 1
@.str.12 = private unnamed_addr constant [21 x i8] c"is5  = %d\09   [0x%x]\0A\00", align 1
@.str.13 = private unnamed_addr constant [23 x i8] c"uic4 = '%c'\09   [0x%x]\0A\00", align 1
@.str.14 = private unnamed_addr constant [19 x i8] c"uis4 = %u  [0x%x]\0A\00", align 1

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @main(i32 noundef %0, ptr noundef %1) #0 {
  %3 = alloca i32, align 4
  %4 = alloca i32, align 4
  %5 = alloca ptr, align 8
  %6 = alloca i8, align 1
  %7 = alloca i16, align 2
  %8 = alloca i8, align 1
  %9 = alloca i8, align 1
  %10 = alloca i8, align 1
  %11 = alloca i8, align 1
  %12 = alloca i8, align 1
  %13 = alloca i8, align 1
  %14 = alloca i16, align 2
  %15 = alloca i32, align 4
  %16 = alloca i32, align 4
  %17 = alloca i32, align 4
  %18 = alloca i32, align 4
  %19 = alloca i32, align 4
  %20 = alloca i32, align 4
  store i32 0, ptr %3, align 4
  store i32 %0, ptr %4, align 4
  store ptr %1, ptr %5, align 8
  %21 = load i32, ptr %4, align 4
  %22 = icmp sge i32 %21, 2
  br i1 %22, label %23, label %28

23:                                               ; preds = %2
  %24 = load ptr, ptr %5, align 8
  %25 = getelementptr inbounds ptr, ptr %24, i64 1
  %26 = load ptr, ptr %25, align 8
  %27 = call i32 @atoi(ptr noundef %26)
  br label %29

28:                                               ; preds = %2
  br label %29

29:                                               ; preds = %28, %23
  %30 = phi i32 [ %27, %23 ], [ 100, %28 ]
  %31 = trunc i32 %30 to i8
  store i8 %31, ptr %6, align 1
  %32 = load i32, ptr %4, align 4
  %33 = icmp sge i32 %32, 3
  br i1 %33, label %34, label %39

34:                                               ; preds = %29
  %35 = load ptr, ptr %5, align 8
  %36 = getelementptr inbounds ptr, ptr %35, i64 2
  %37 = load ptr, ptr %36, align 8
  %38 = call i32 @atoi(ptr noundef %37)
  br label %40

39:                                               ; preds = %29
  br label %40

40:                                               ; preds = %39, %34
  %41 = phi i32 [ %38, %34 ], [ -769, %39 ]
  %42 = trunc i32 %41 to i16
  store i16 %42, ptr %7, align 2
  %43 = load i8, ptr %6, align 1
  store i8 %43, ptr %8, align 1
  %44 = load i16, ptr %7, align 2
  %45 = trunc i16 %44 to i8
  store i8 %45, ptr %9, align 1
  %46 = load i8, ptr %9, align 1
  %47 = zext i8 %46 to i32
  %48 = add nsw i32 %47, 1
  %49 = trunc i32 %48 to i8
  store i8 %49, ptr %10, align 1
  %50 = load i8, ptr %9, align 1
  store i8 %50, ptr %11, align 1
  %51 = load i8, ptr %9, align 1
  %52 = zext i8 %51 to i32
  %53 = add i32 %52, 1
  %54 = trunc i32 %53 to i8
  store i8 %54, ptr %12, align 1
  %55 = load i8, ptr %6, align 1
  store i8 %55, ptr %13, align 1
  %56 = load i16, ptr %7, align 2
  store i16 %56, ptr %14, align 2
  %57 = load i8, ptr %6, align 1
  %58 = sext i8 %57 to i32
  store i32 %58, ptr %15, align 4
  %59 = load i16, ptr %7, align 2
  %60 = sext i16 %59 to i32
  store i32 %60, ptr %16, align 4
  %61 = load i8, ptr %9, align 1
  %62 = zext i8 %61 to i32
  %63 = add nsw i32 %62, 1
  store i32 %63, ptr %17, align 4
  %64 = load i8, ptr %11, align 1
  %65 = sext i8 %64 to i32
  %66 = add nsw i32 %65, 1
  store i32 %66, ptr %18, align 4
  %67 = load i8, ptr %6, align 1
  %68 = sext i8 %67 to i32
  store i32 %68, ptr %19, align 4
  %69 = load i16, ptr %7, align 2
  %70 = sext i16 %69 to i32
  store i32 %70, ptr %20, align 4
  %71 = load i8, ptr %8, align 1
  %72 = zext i8 %71 to i32
  %73 = load i8, ptr %8, align 1
  %74 = zext i8 %73 to i32
  %75 = call i32 (ptr, ...) @printf(ptr noundef @.str, i32 noundef %72, i32 noundef %74)
  %76 = load i8, ptr %9, align 1
  %77 = zext i8 %76 to i32
  %78 = load i8, ptr %9, align 1
  %79 = zext i8 %78 to i32
  %80 = call i32 (ptr, ...) @printf(ptr noundef @.str.1, i32 noundef %77, i32 noundef %79)
  %81 = load i8, ptr %10, align 1
  %82 = zext i8 %81 to i32
  %83 = load i8, ptr %10, align 1
  %84 = zext i8 %83 to i32
  %85 = call i32 (ptr, ...) @printf(ptr noundef @.str.2, i32 noundef %82, i32 noundef %84)
  %86 = load i8, ptr %11, align 1
  %87 = sext i8 %86 to i32
  %88 = load i8, ptr %11, align 1
  %89 = sext i8 %88 to i32
  %90 = call i32 (ptr, ...) @printf(ptr noundef @.str.3, i32 noundef %87, i32 noundef %89)
  %91 = load i8, ptr %12, align 1
  %92 = sext i8 %91 to i32
  %93 = load i8, ptr %12, align 1
  %94 = sext i8 %93 to i32
  %95 = call i32 (ptr, ...) @printf(ptr noundef @.str.4, i32 noundef %92, i32 noundef %94)
  %96 = load i8, ptr %6, align 1
  %97 = sext i8 %96 to i32
  %98 = load i8, ptr %6, align 1
  %99 = sext i8 %98 to i32
  %100 = call i32 (ptr, ...) @printf(ptr noundef @.str.5, i32 noundef %97, i32 noundef %99)
  %101 = load i16, ptr %7, align 2
  %102 = sext i16 %101 to i32
  %103 = load i16, ptr %7, align 2
  %104 = sext i16 %103 to i32
  %105 = call i32 (ptr, ...) @printf(ptr noundef @.str.6, i32 noundef %102, i32 noundef %104)
  %106 = load i8, ptr %13, align 1
  %107 = zext i8 %106 to i32
  %108 = load i8, ptr %13, align 1
  %109 = zext i8 %108 to i32
  %110 = call i32 (ptr, ...) @printf(ptr noundef @.str.7, i32 noundef %107, i32 noundef %109)
  %111 = load i16, ptr %14, align 2
  %112 = zext i16 %111 to i32
  %113 = load i16, ptr %14, align 2
  %114 = zext i16 %113 to i32
  %115 = call i32 (ptr, ...) @printf(ptr noundef @.str.8, i32 noundef %112, i32 noundef %114)
  %116 = load i32, ptr %15, align 4
  %117 = load i32, ptr %15, align 4
  %118 = call i32 (ptr, ...) @printf(ptr noundef @.str.9, i32 noundef %116, i32 noundef %117)
  %119 = load i32, ptr %16, align 4
  %120 = load i32, ptr %16, align 4
  %121 = call i32 (ptr, ...) @printf(ptr noundef @.str.10, i32 noundef %119, i32 noundef %120)
  %122 = load i32, ptr %17, align 4
  %123 = load i32, ptr %17, align 4
  %124 = call i32 (ptr, ...) @printf(ptr noundef @.str.11, i32 noundef %122, i32 noundef %123)
  %125 = load i32, ptr %18, align 4
  %126 = load i32, ptr %18, align 4
  %127 = call i32 (ptr, ...) @printf(ptr noundef @.str.12, i32 noundef %125, i32 noundef %126)
  %128 = load i32, ptr %19, align 4
  %129 = load i32, ptr %19, align 4
  %130 = call i32 (ptr, ...) @printf(ptr noundef @.str.13, i32 noundef %128, i32 noundef %129)
  %131 = load i32, ptr %20, align 4
  %132 = load i32, ptr %20, align 4
  %133 = call i32 (ptr, ...) @printf(ptr noundef @.str.14, i32 noundef %131, i32 noundef %132)
  ret i32 0
}

declare dso_local i32 @atoi(ptr noundef) #1

declare dso_local i32 @printf(ptr noundef, ...) #1

attributes #0 = { noinline nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5}
!llvm.ident = !{!6}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)", isOptimized: false, runtimeVersion: 0, emissionKind: NoDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "E:\\llvm-test-suite\\SingleSource\\UnitTests/2002-05-02-CastTest.c", directory: "E:/project")
!2 = !{i32 2, !"Debug Info Version", i32 3}
!3 = !{i32 8, !"PIC Level", i32 2}
!4 = !{i32 7, !"uwtable", i32 2}
!5 = !{i32 1, !"MaxTLSAlign", i32 65536}
!6 = !{!"clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)"}
