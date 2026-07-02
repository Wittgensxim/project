; ModuleID = 'E:\llvm-test-suite\SingleSource\Benchmarks\Misc\ffbench.c'
source_filename = "E:\\llvm-test-suite\\SingleSource\\Benchmarks\\Misc\\ffbench.c"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-w64-windows-gnu"

@main.nsize = internal global [3 x i32] zeroinitializer, align 4
@.str = private unnamed_addr constant [28 x i8] c"Can't allocate data array.\0A\00", align 1
@.str.1 = private unnamed_addr constant [48 x i8] c"Wrong answer at (%d,%d)!  Expected %d, got %d.\0A\00", align 1
@.str.2 = private unnamed_addr constant [35 x i8] c"%d passes.  No errors in results.\0A\00", align 1
@.str.3 = private unnamed_addr constant [35 x i8] c"%d passes.  %d errors in results.\0A\00", align 1

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  %4 = alloca i32, align 4
  %5 = alloca i32, align 4
  %6 = alloca i32, align 4
  %7 = alloca i32, align 4
  %8 = alloca i32, align 4
  %9 = alloca ptr, align 8
  %10 = alloca i32, align 4
  %11 = alloca i32, align 4
  %12 = alloca double, align 8
  %13 = alloca double, align 8
  %14 = alloca double, align 8
  %15 = alloca double, align 8
  %16 = alloca double, align 8
  %17 = alloca double, align 8
  %18 = alloca double, align 8
  %19 = alloca double, align 8
  %20 = alloca double, align 8
  %21 = alloca double, align 8
  store i32 0, ptr %1, align 4
  store i32 63, ptr %7, align 4
  store i32 256, ptr %8, align 4
  %22 = load i32, ptr %8, align 4
  %23 = load i32, ptr %8, align 4
  %24 = mul nsw i32 %22, %23
  store i32 %24, ptr %10, align 4
  %25 = load i32, ptr %10, align 4
  %26 = add nsw i32 %25, 1
  %27 = mul nsw i32 %26, 2
  %28 = sext i32 %27 to i64
  %29 = mul i64 %28, 8
  %30 = trunc i64 %29 to i32
  store i32 %30, ptr %11, align 4
  %31 = load i32, ptr %8, align 4
  store i32 %31, ptr getelementptr inbounds nuw (i8, ptr @main.nsize, i64 8), align 4
  store i32 %31, ptr getelementptr inbounds nuw (i8, ptr @main.nsize, i64 4), align 4
  %32 = load i32, ptr %11, align 4
  %33 = sext i32 %32 to i64
  %34 = call ptr @malloc(i64 noundef %33) #7
  store ptr %34, ptr %9, align 8
  %35 = load ptr, ptr %9, align 8
  %36 = icmp eq ptr %35, null
  br i1 %36, label %37, label %40

37:                                               ; preds = %0
  %38 = call ptr @__acrt_iob_func(i32 noundef 2)
  %39 = call i32 (ptr, ptr, ...) @fprintf(ptr noundef %38, ptr noundef @.str) #8
  call void @exit(i32 noundef 1) #9
  unreachable

40:                                               ; preds = %0
  %41 = load ptr, ptr %9, align 8
  %42 = load i32, ptr %11, align 4
  %43 = sext i32 %42 to i64
  call void @llvm.memset.p0.i64(ptr align 8 %41, i8 0, i64 %43, i1 false)
  store i32 0, ptr %2, align 4
  br label %44

44:                                               ; preds = %77, %40
  %45 = load i32, ptr %2, align 4
  %46 = load i32, ptr %8, align 4
  %47 = icmp slt i32 %45, %46
  br i1 %47, label %48, label %80

48:                                               ; preds = %44
  store i32 0, ptr %3, align 4
  br label %49

49:                                               ; preds = %73, %48
  %50 = load i32, ptr %3, align 4
  %51 = load i32, ptr %8, align 4
  %52 = icmp slt i32 %50, %51
  br i1 %52, label %53, label %76

53:                                               ; preds = %49
  %54 = load i32, ptr %2, align 4
  %55 = and i32 %54, 15
  %56 = icmp eq i32 %55, 8
  br i1 %56, label %61, label %57

57:                                               ; preds = %53
  %58 = load i32, ptr %3, align 4
  %59 = and i32 %58, 15
  %60 = icmp eq i32 %59, 8
  br i1 %60, label %61, label %72

61:                                               ; preds = %57, %53
  %62 = load ptr, ptr %9, align 8
  %63 = load i32, ptr %8, align 4
  %64 = load i32, ptr %2, align 4
  %65 = mul nsw i32 %63, %64
  %66 = load i32, ptr %3, align 4
  %67 = add nsw i32 %65, %66
  %68 = mul nsw i32 %67, 2
  %69 = add nsw i32 1, %68
  %70 = sext i32 %69 to i64
  %71 = getelementptr inbounds double, ptr %62, i64 %70
  store double 1.280000e+02, ptr %71, align 8
  br label %72

72:                                               ; preds = %61, %57
  br label %73

73:                                               ; preds = %72
  %74 = load i32, ptr %3, align 4
  %75 = add nsw i32 %74, 1
  store i32 %75, ptr %3, align 4
  br label %49, !llvm.loop !7

76:                                               ; preds = %49
  br label %77

77:                                               ; preds = %76
  %78 = load i32, ptr %2, align 4
  %79 = add nsw i32 %78, 1
  store i32 %79, ptr %2, align 4
  br label %44, !llvm.loop !9

80:                                               ; preds = %44
  store i32 0, ptr %2, align 4
  br label %81

81:                                               ; preds = %88, %80
  %82 = load i32, ptr %2, align 4
  %83 = load i32, ptr %7, align 4
  %84 = icmp slt i32 %82, %83
  br i1 %84, label %85, label %91

85:                                               ; preds = %81
  %86 = load ptr, ptr %9, align 8
  call void @fourn(ptr noundef %86, ptr noundef @main.nsize, i32 noundef 2, i32 noundef 1)
  %87 = load ptr, ptr %9, align 8
  call void @fourn(ptr noundef %87, ptr noundef @main.nsize, i32 noundef 2, i32 noundef -1)
  br label %88

88:                                               ; preds = %85
  %89 = load i32, ptr %2, align 4
  %90 = add nsw i32 %89, 1
  store i32 %90, ptr %2, align 4
  br label %81, !llvm.loop !10

91:                                               ; preds = %81
  store double 1.000000e+10, ptr %14, align 8
  store double -1.000000e+10, ptr %15, align 8
  store double 1.000000e+10, ptr %16, align 8
  store double -1.000000e+10, ptr %17, align 8
  store double 0.000000e+00, ptr %20, align 8
  store double 0.000000e+00, ptr %21, align 8
  store i32 1, ptr %2, align 4
  br label %92

92:                                               ; preds = %150, %91
  %93 = load i32, ptr %2, align 4
  %94 = load i32, ptr %10, align 4
  %95 = icmp sle i32 %93, %94
  br i1 %95, label %96, label %153

96:                                               ; preds = %92
  %97 = load ptr, ptr %9, align 8
  %98 = load i32, ptr %2, align 4
  %99 = sext i32 %98 to i64
  %100 = getelementptr inbounds double, ptr %97, i64 %99
  %101 = load double, ptr %100, align 8
  store double %101, ptr %18, align 8
  %102 = load ptr, ptr %9, align 8
  %103 = load i32, ptr %2, align 4
  %104 = add nsw i32 %103, 1
  %105 = sext i32 %104 to i64
  %106 = getelementptr inbounds double, ptr %102, i64 %105
  %107 = load double, ptr %106, align 8
  store double %107, ptr %19, align 8
  %108 = load double, ptr %18, align 8
  %109 = load double, ptr %20, align 8
  %110 = fadd double %109, %108
  store double %110, ptr %20, align 8
  %111 = load double, ptr %19, align 8
  %112 = load double, ptr %21, align 8
  %113 = fadd double %112, %111
  store double %113, ptr %21, align 8
  %114 = load double, ptr %18, align 8
  %115 = load double, ptr %14, align 8
  %116 = fcmp ole double %114, %115
  br i1 %116, label %117, label %119

117:                                              ; preds = %96
  %118 = load double, ptr %18, align 8
  br label %121

119:                                              ; preds = %96
  %120 = load double, ptr %14, align 8
  br label %121

121:                                              ; preds = %119, %117
  %122 = phi double [ %118, %117 ], [ %120, %119 ]
  store double %122, ptr %14, align 8
  %123 = load double, ptr %18, align 8
  %124 = load double, ptr %15, align 8
  %125 = fcmp ogt double %123, %124
  br i1 %125, label %126, label %128

126:                                              ; preds = %121
  %127 = load double, ptr %18, align 8
  br label %130

128:                                              ; preds = %121
  %129 = load double, ptr %15, align 8
  br label %130

130:                                              ; preds = %128, %126
  %131 = phi double [ %127, %126 ], [ %129, %128 ]
  store double %131, ptr %15, align 8
  %132 = load double, ptr %19, align 8
  %133 = load double, ptr %16, align 8
  %134 = fcmp ole double %132, %133
  br i1 %134, label %135, label %137

135:                                              ; preds = %130
  %136 = load double, ptr %19, align 8
  br label %139

137:                                              ; preds = %130
  %138 = load double, ptr %16, align 8
  br label %139

139:                                              ; preds = %137, %135
  %140 = phi double [ %136, %135 ], [ %138, %137 ]
  store double %140, ptr %16, align 8
  %141 = load double, ptr %19, align 8
  %142 = load double, ptr %17, align 8
  %143 = fcmp ogt double %141, %142
  br i1 %143, label %144, label %146

144:                                              ; preds = %139
  %145 = load double, ptr %19, align 8
  br label %148

146:                                              ; preds = %139
  %147 = load double, ptr %17, align 8
  br label %148

148:                                              ; preds = %146, %144
  %149 = phi double [ %145, %144 ], [ %147, %146 ]
  store double %149, ptr %17, align 8
  br label %150

150:                                              ; preds = %148
  %151 = load i32, ptr %2, align 4
  %152 = add nsw i32 %151, 2
  store i32 %152, ptr %2, align 4
  br label %92, !llvm.loop !11

153:                                              ; preds = %92
  %154 = load double, ptr %14, align 8
  store double %154, ptr %12, align 8
  %155 = load double, ptr %15, align 8
  %156 = load double, ptr %14, align 8
  %157 = fsub double %155, %156
  %158 = fdiv double 2.550000e+02, %157
  store double %158, ptr %13, align 8
  store i32 0, ptr %6, align 4
  store i32 0, ptr %2, align 4
  br label %159

159:                                              ; preds = %213, %153
  %160 = load i32, ptr %2, align 4
  %161 = load i32, ptr %8, align 4
  %162 = icmp slt i32 %160, %161
  br i1 %162, label %163, label %216

163:                                              ; preds = %159
  store i32 0, ptr %3, align 4
  br label %164

164:                                              ; preds = %209, %163
  %165 = load i32, ptr %3, align 4
  %166 = load i32, ptr %8, align 4
  %167 = icmp slt i32 %165, %166
  br i1 %167, label %168, label %212

168:                                              ; preds = %164
  %169 = load ptr, ptr %9, align 8
  %170 = load i32, ptr %8, align 4
  %171 = load i32, ptr %2, align 4
  %172 = mul nsw i32 %170, %171
  %173 = load i32, ptr %3, align 4
  %174 = add nsw i32 %172, %173
  %175 = mul nsw i32 %174, 2
  %176 = add nsw i32 1, %175
  %177 = sext i32 %176 to i64
  %178 = getelementptr inbounds double, ptr %169, i64 %177
  %179 = load double, ptr %178, align 8
  %180 = load double, ptr %12, align 8
  %181 = fsub double %179, %180
  %182 = load double, ptr %13, align 8
  %183 = fmul double %181, %182
  %184 = fptosi double %183 to i32
  store i32 %184, ptr %4, align 4
  %185 = load i32, ptr %2, align 4
  %186 = and i32 %185, 15
  %187 = icmp eq i32 %186, 8
  br i1 %187, label %192, label %188

188:                                              ; preds = %168
  %189 = load i32, ptr %3, align 4
  %190 = and i32 %189, 15
  %191 = icmp eq i32 %190, 8
  br label %192

192:                                              ; preds = %188, %168
  %193 = phi i1 [ true, %168 ], [ %191, %188 ]
  %194 = zext i1 %193 to i64
  %195 = select i1 %193, i32 255, i32 0
  store i32 %195, ptr %5, align 4
  %196 = load i32, ptr %4, align 4
  %197 = load i32, ptr %5, align 4
  %198 = icmp ne i32 %196, %197
  br i1 %198, label %199, label %208

199:                                              ; preds = %192
  %200 = load i32, ptr %6, align 4
  %201 = add nsw i32 %200, 1
  store i32 %201, ptr %6, align 4
  %202 = call ptr @__acrt_iob_func(i32 noundef 2)
  %203 = load i32, ptr %2, align 4
  %204 = load i32, ptr %3, align 4
  %205 = load i32, ptr %5, align 4
  %206 = load i32, ptr %4, align 4
  %207 = call i32 (ptr, ptr, ...) @fprintf(ptr noundef %202, ptr noundef @.str.1, i32 noundef %203, i32 noundef %204, i32 noundef %205, i32 noundef %206) #8
  br label %208

208:                                              ; preds = %199, %192
  br label %209

209:                                              ; preds = %208
  %210 = load i32, ptr %3, align 4
  %211 = add nsw i32 %210, 1
  store i32 %211, ptr %3, align 4
  br label %164, !llvm.loop !12

212:                                              ; preds = %164
  br label %213

213:                                              ; preds = %212
  %214 = load i32, ptr %2, align 4
  %215 = add nsw i32 %214, 1
  store i32 %215, ptr %2, align 4
  br label %159, !llvm.loop !13

216:                                              ; preds = %159
  %217 = load i32, ptr %6, align 4
  %218 = icmp eq i32 %217, 0
  br i1 %218, label %219, label %223

219:                                              ; preds = %216
  %220 = call ptr @__acrt_iob_func(i32 noundef 2)
  %221 = load i32, ptr %7, align 4
  %222 = call i32 (ptr, ptr, ...) @fprintf(ptr noundef %220, ptr noundef @.str.2, i32 noundef %221) #8
  br label %228

223:                                              ; preds = %216
  %224 = call ptr @__acrt_iob_func(i32 noundef 2)
  %225 = load i32, ptr %7, align 4
  %226 = load i32, ptr %6, align 4
  %227 = call i32 (ptr, ptr, ...) @fprintf(ptr noundef %224, ptr noundef @.str.3, i32 noundef %225, i32 noundef %226) #8
  br label %228

228:                                              ; preds = %223, %219
  ret i32 0
}

; Function Attrs: allocsize(0)
declare dso_local ptr @malloc(i64 noundef) #1

; Function Attrs: nounwind
declare dso_local i32 @fprintf(ptr noundef, ptr noundef, ...) #2

declare dllimport ptr @__acrt_iob_func(i32 noundef) #3

; Function Attrs: noreturn nounwind
declare dso_local void @exit(i32 noundef) #4

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: write)
declare void @llvm.memset.p0.i64(ptr writeonly captures(none), i8, i64, i1 immarg) #5

; Function Attrs: noinline nounwind uwtable
define internal void @fourn(ptr noundef %0, ptr noundef %1, i32 noundef %2, i32 noundef %3) #0 {
  %5 = alloca ptr, align 8
  %6 = alloca ptr, align 8
  %7 = alloca i32, align 4
  %8 = alloca i32, align 4
  %9 = alloca i32, align 4
  %10 = alloca i32, align 4
  %11 = alloca i32, align 4
  %12 = alloca i32, align 4
  %13 = alloca i32, align 4
  %14 = alloca i32, align 4
  %15 = alloca i32, align 4
  %16 = alloca i32, align 4
  %17 = alloca i32, align 4
  %18 = alloca i32, align 4
  %19 = alloca i32, align 4
  %20 = alloca i32, align 4
  %21 = alloca i32, align 4
  %22 = alloca i32, align 4
  %23 = alloca i32, align 4
  %24 = alloca i32, align 4
  %25 = alloca i32, align 4
  %26 = alloca i32, align 4
  %27 = alloca double, align 8
  %28 = alloca double, align 8
  %29 = alloca double, align 8
  %30 = alloca double, align 8
  %31 = alloca double, align 8
  %32 = alloca double, align 8
  %33 = alloca double, align 8
  %34 = alloca double, align 8
  store ptr %0, ptr %5, align 8
  store ptr %1, ptr %6, align 8
  store i32 %2, ptr %7, align 4
  store i32 %3, ptr %8, align 4
  store i32 1, ptr %26, align 4
  store i32 1, ptr %20, align 4
  br label %35

35:                                               ; preds = %47, %4
  %36 = load i32, ptr %20, align 4
  %37 = load i32, ptr %7, align 4
  %38 = icmp sle i32 %36, %37
  br i1 %38, label %39, label %50

39:                                               ; preds = %35
  %40 = load ptr, ptr %6, align 8
  %41 = load i32, ptr %20, align 4
  %42 = sext i32 %41 to i64
  %43 = getelementptr inbounds i32, ptr %40, i64 %42
  %44 = load i32, ptr %43, align 4
  %45 = load i32, ptr %26, align 4
  %46 = mul nsw i32 %45, %44
  store i32 %46, ptr %26, align 4
  br label %47

47:                                               ; preds = %39
  %48 = load i32, ptr %20, align 4
  %49 = add nsw i32 %48, 1
  store i32 %49, ptr %20, align 4
  br label %35, !llvm.loop !14

50:                                               ; preds = %35
  store i32 1, ptr %24, align 4
  %51 = load i32, ptr %7, align 4
  store i32 %51, ptr %20, align 4
  br label %52

52:                                               ; preds = %337, %50
  %53 = load i32, ptr %20, align 4
  %54 = icmp sge i32 %53, 1
  br i1 %54, label %55, label %340

55:                                               ; preds = %52
  %56 = load ptr, ptr %6, align 8
  %57 = load i32, ptr %20, align 4
  %58 = sext i32 %57 to i64
  %59 = getelementptr inbounds i32, ptr %56, i64 %58
  %60 = load i32, ptr %59, align 4
  store i32 %60, ptr %23, align 4
  %61 = load i32, ptr %26, align 4
  %62 = load i32, ptr %23, align 4
  %63 = load i32, ptr %24, align 4
  %64 = mul nsw i32 %62, %63
  %65 = sdiv i32 %61, %64
  store i32 %65, ptr %25, align 4
  %66 = load i32, ptr %24, align 4
  %67 = shl i32 %66, 1
  store i32 %67, ptr %14, align 4
  %68 = load i32, ptr %14, align 4
  %69 = load i32, ptr %23, align 4
  %70 = mul nsw i32 %68, %69
  store i32 %70, ptr %15, align 4
  %71 = load i32, ptr %15, align 4
  %72 = load i32, ptr %25, align 4
  %73 = mul nsw i32 %71, %72
  store i32 %73, ptr %16, align 4
  store i32 1, ptr %12, align 4
  store i32 1, ptr %10, align 4
  br label %74

74:                                               ; preds = %177, %55
  %75 = load i32, ptr %10, align 4
  %76 = load i32, ptr %15, align 4
  %77 = icmp sle i32 %75, %76
  br i1 %77, label %78, label %181

78:                                               ; preds = %74
  %79 = load i32, ptr %10, align 4
  %80 = load i32, ptr %12, align 4
  %81 = icmp slt i32 %79, %80
  br i1 %81, label %82, label %154

82:                                               ; preds = %78
  %83 = load i32, ptr %10, align 4
  store i32 %83, ptr %9, align 4
  br label %84

84:                                               ; preds = %150, %82
  %85 = load i32, ptr %9, align 4
  %86 = load i32, ptr %10, align 4
  %87 = load i32, ptr %14, align 4
  %88 = add nsw i32 %86, %87
  %89 = sub nsw i32 %88, 2
  %90 = icmp sle i32 %85, %89
  br i1 %90, label %91, label %153

91:                                               ; preds = %84
  %92 = load i32, ptr %9, align 4
  store i32 %92, ptr %11, align 4
  br label %93

93:                                               ; preds = %145, %91
  %94 = load i32, ptr %11, align 4
  %95 = load i32, ptr %16, align 4
  %96 = icmp sle i32 %94, %95
  br i1 %96, label %97, label %149

97:                                               ; preds = %93
  %98 = load i32, ptr %12, align 4
  %99 = load i32, ptr %11, align 4
  %100 = add nsw i32 %98, %99
  %101 = load i32, ptr %10, align 4
  %102 = sub nsw i32 %100, %101
  store i32 %102, ptr %13, align 4
  %103 = load ptr, ptr %5, align 8
  %104 = load i32, ptr %11, align 4
  %105 = sext i32 %104 to i64
  %106 = getelementptr inbounds double, ptr %103, i64 %105
  %107 = load double, ptr %106, align 8
  store double %107, ptr %28, align 8
  %108 = load ptr, ptr %5, align 8
  %109 = load i32, ptr %13, align 4
  %110 = sext i32 %109 to i64
  %111 = getelementptr inbounds double, ptr %108, i64 %110
  %112 = load double, ptr %111, align 8
  %113 = load ptr, ptr %5, align 8
  %114 = load i32, ptr %11, align 4
  %115 = sext i32 %114 to i64
  %116 = getelementptr inbounds double, ptr %113, i64 %115
  store double %112, ptr %116, align 8
  %117 = load double, ptr %28, align 8
  %118 = load ptr, ptr %5, align 8
  %119 = load i32, ptr %13, align 4
  %120 = sext i32 %119 to i64
  %121 = getelementptr inbounds double, ptr %118, i64 %120
  store double %117, ptr %121, align 8
  %122 = load ptr, ptr %5, align 8
  %123 = load i32, ptr %11, align 4
  %124 = add nsw i32 %123, 1
  %125 = sext i32 %124 to i64
  %126 = getelementptr inbounds double, ptr %122, i64 %125
  %127 = load double, ptr %126, align 8
  store double %127, ptr %28, align 8
  %128 = load ptr, ptr %5, align 8
  %129 = load i32, ptr %13, align 4
  %130 = add nsw i32 %129, 1
  %131 = sext i32 %130 to i64
  %132 = getelementptr inbounds double, ptr %128, i64 %131
  %133 = load double, ptr %132, align 8
  %134 = load ptr, ptr %5, align 8
  %135 = load i32, ptr %11, align 4
  %136 = add nsw i32 %135, 1
  %137 = sext i32 %136 to i64
  %138 = getelementptr inbounds double, ptr %134, i64 %137
  store double %133, ptr %138, align 8
  %139 = load double, ptr %28, align 8
  %140 = load ptr, ptr %5, align 8
  %141 = load i32, ptr %13, align 4
  %142 = add nsw i32 %141, 1
  %143 = sext i32 %142 to i64
  %144 = getelementptr inbounds double, ptr %140, i64 %143
  store double %139, ptr %144, align 8
  br label %145

145:                                              ; preds = %97
  %146 = load i32, ptr %15, align 4
  %147 = load i32, ptr %11, align 4
  %148 = add nsw i32 %147, %146
  store i32 %148, ptr %11, align 4
  br label %93, !llvm.loop !15

149:                                              ; preds = %93
  br label %150

150:                                              ; preds = %149
  %151 = load i32, ptr %9, align 4
  %152 = add nsw i32 %151, 2
  store i32 %152, ptr %9, align 4
  br label %84, !llvm.loop !16

153:                                              ; preds = %84
  br label %154

154:                                              ; preds = %153, %78
  %155 = load i32, ptr %15, align 4
  %156 = ashr i32 %155, 1
  store i32 %156, ptr %19, align 4
  br label %157

157:                                              ; preds = %167, %154
  %158 = load i32, ptr %19, align 4
  %159 = load i32, ptr %14, align 4
  %160 = icmp sge i32 %158, %159
  br i1 %160, label %161, label %165

161:                                              ; preds = %157
  %162 = load i32, ptr %12, align 4
  %163 = load i32, ptr %19, align 4
  %164 = icmp sgt i32 %162, %163
  br label %165

165:                                              ; preds = %161, %157
  %166 = phi i1 [ false, %157 ], [ %164, %161 ]
  br i1 %166, label %167, label %173

167:                                              ; preds = %165
  %168 = load i32, ptr %19, align 4
  %169 = load i32, ptr %12, align 4
  %170 = sub nsw i32 %169, %168
  store i32 %170, ptr %12, align 4
  %171 = load i32, ptr %19, align 4
  %172 = ashr i32 %171, 1
  store i32 %172, ptr %19, align 4
  br label %157, !llvm.loop !17

173:                                              ; preds = %165
  %174 = load i32, ptr %19, align 4
  %175 = load i32, ptr %12, align 4
  %176 = add nsw i32 %175, %174
  store i32 %176, ptr %12, align 4
  br label %177

177:                                              ; preds = %173
  %178 = load i32, ptr %14, align 4
  %179 = load i32, ptr %10, align 4
  %180 = add nsw i32 %179, %178
  store i32 %180, ptr %10, align 4
  br label %74, !llvm.loop !18

181:                                              ; preds = %74
  %182 = load i32, ptr %14, align 4
  store i32 %182, ptr %17, align 4
  br label %183

183:                                              ; preds = %331, %181
  %184 = load i32, ptr %17, align 4
  %185 = load i32, ptr %15, align 4
  %186 = icmp slt i32 %184, %185
  br i1 %186, label %187, label %333

187:                                              ; preds = %183
  %188 = load i32, ptr %17, align 4
  %189 = shl i32 %188, 1
  store i32 %189, ptr %18, align 4
  %190 = load i32, ptr %8, align 4
  %191 = sitofp i32 %190 to double
  %192 = fmul double %191, f0x401921FB54442D1C
  %193 = load i32, ptr %18, align 4
  %194 = load i32, ptr %14, align 4
  %195 = sdiv i32 %193, %194
  %196 = sitofp i32 %195 to double
  %197 = fdiv double %192, %196
  store double %197, ptr %29, align 8
  %198 = load double, ptr %29, align 8
  %199 = fmul double 5.000000e-01, %198
  %200 = call double @sin(double noundef %199) #8
  store double %200, ptr %34, align 8
  %201 = load double, ptr %34, align 8
  %202 = fmul double -2.000000e+00, %201
  %203 = load double, ptr %34, align 8
  %204 = fmul double %202, %203
  store double %204, ptr %32, align 8
  %205 = load double, ptr %29, align 8
  %206 = call double @sin(double noundef %205) #8
  store double %206, ptr %31, align 8
  store double 1.000000e+00, ptr %33, align 8
  store double 0.000000e+00, ptr %30, align 8
  store i32 1, ptr %11, align 4
  br label %207

207:                                              ; preds = %327, %187
  %208 = load i32, ptr %11, align 4
  %209 = load i32, ptr %17, align 4
  %210 = icmp sle i32 %208, %209
  br i1 %210, label %211, label %331

211:                                              ; preds = %207
  %212 = load i32, ptr %11, align 4
  store i32 %212, ptr %9, align 4
  br label %213

213:                                              ; preds = %306, %211
  %214 = load i32, ptr %9, align 4
  %215 = load i32, ptr %11, align 4
  %216 = load i32, ptr %14, align 4
  %217 = add nsw i32 %215, %216
  %218 = sub nsw i32 %217, 2
  %219 = icmp sle i32 %214, %218
  br i1 %219, label %220, label %309

220:                                              ; preds = %213
  %221 = load i32, ptr %9, align 4
  store i32 %221, ptr %10, align 4
  br label %222

222:                                              ; preds = %301, %220
  %223 = load i32, ptr %10, align 4
  %224 = load i32, ptr %16, align 4
  %225 = icmp sle i32 %223, %224
  br i1 %225, label %226, label %305

226:                                              ; preds = %222
  %227 = load i32, ptr %10, align 4
  store i32 %227, ptr %21, align 4
  %228 = load i32, ptr %21, align 4
  %229 = load i32, ptr %17, align 4
  %230 = add nsw i32 %228, %229
  store i32 %230, ptr %22, align 4
  %231 = load double, ptr %33, align 8
  %232 = load ptr, ptr %5, align 8
  %233 = load i32, ptr %22, align 4
  %234 = sext i32 %233 to i64
  %235 = getelementptr inbounds double, ptr %232, i64 %234
  %236 = load double, ptr %235, align 8
  %237 = load double, ptr %30, align 8
  %238 = load ptr, ptr %5, align 8
  %239 = load i32, ptr %22, align 4
  %240 = add nsw i32 %239, 1
  %241 = sext i32 %240 to i64
  %242 = getelementptr inbounds double, ptr %238, i64 %241
  %243 = load double, ptr %242, align 8
  %244 = fmul double %237, %243
  %245 = fneg double %244
  %246 = call double @llvm.fmuladd.f64(double %231, double %236, double %245)
  store double %246, ptr %28, align 8
  %247 = load double, ptr %33, align 8
  %248 = load ptr, ptr %5, align 8
  %249 = load i32, ptr %22, align 4
  %250 = add nsw i32 %249, 1
  %251 = sext i32 %250 to i64
  %252 = getelementptr inbounds double, ptr %248, i64 %251
  %253 = load double, ptr %252, align 8
  %254 = load double, ptr %30, align 8
  %255 = load ptr, ptr %5, align 8
  %256 = load i32, ptr %22, align 4
  %257 = sext i32 %256 to i64
  %258 = getelementptr inbounds double, ptr %255, i64 %257
  %259 = load double, ptr %258, align 8
  %260 = fmul double %254, %259
  %261 = call double @llvm.fmuladd.f64(double %247, double %253, double %260)
  store double %261, ptr %27, align 8
  %262 = load ptr, ptr %5, align 8
  %263 = load i32, ptr %21, align 4
  %264 = sext i32 %263 to i64
  %265 = getelementptr inbounds double, ptr %262, i64 %264
  %266 = load double, ptr %265, align 8
  %267 = load double, ptr %28, align 8
  %268 = fsub double %266, %267
  %269 = load ptr, ptr %5, align 8
  %270 = load i32, ptr %22, align 4
  %271 = sext i32 %270 to i64
  %272 = getelementptr inbounds double, ptr %269, i64 %271
  store double %268, ptr %272, align 8
  %273 = load ptr, ptr %5, align 8
  %274 = load i32, ptr %21, align 4
  %275 = add nsw i32 %274, 1
  %276 = sext i32 %275 to i64
  %277 = getelementptr inbounds double, ptr %273, i64 %276
  %278 = load double, ptr %277, align 8
  %279 = load double, ptr %27, align 8
  %280 = fsub double %278, %279
  %281 = load ptr, ptr %5, align 8
  %282 = load i32, ptr %22, align 4
  %283 = add nsw i32 %282, 1
  %284 = sext i32 %283 to i64
  %285 = getelementptr inbounds double, ptr %281, i64 %284
  store double %280, ptr %285, align 8
  %286 = load double, ptr %28, align 8
  %287 = load ptr, ptr %5, align 8
  %288 = load i32, ptr %21, align 4
  %289 = sext i32 %288 to i64
  %290 = getelementptr inbounds double, ptr %287, i64 %289
  %291 = load double, ptr %290, align 8
  %292 = fadd double %291, %286
  store double %292, ptr %290, align 8
  %293 = load double, ptr %27, align 8
  %294 = load ptr, ptr %5, align 8
  %295 = load i32, ptr %21, align 4
  %296 = add nsw i32 %295, 1
  %297 = sext i32 %296 to i64
  %298 = getelementptr inbounds double, ptr %294, i64 %297
  %299 = load double, ptr %298, align 8
  %300 = fadd double %299, %293
  store double %300, ptr %298, align 8
  br label %301

301:                                              ; preds = %226
  %302 = load i32, ptr %18, align 4
  %303 = load i32, ptr %10, align 4
  %304 = add nsw i32 %303, %302
  store i32 %304, ptr %10, align 4
  br label %222, !llvm.loop !19

305:                                              ; preds = %222
  br label %306

306:                                              ; preds = %305
  %307 = load i32, ptr %9, align 4
  %308 = add nsw i32 %307, 2
  store i32 %308, ptr %9, align 4
  br label %213, !llvm.loop !20

309:                                              ; preds = %213
  %310 = load double, ptr %33, align 8
  store double %310, ptr %34, align 8
  %311 = load double, ptr %32, align 8
  %312 = load double, ptr %30, align 8
  %313 = load double, ptr %31, align 8
  %314 = fmul double %312, %313
  %315 = fneg double %314
  %316 = call double @llvm.fmuladd.f64(double %310, double %311, double %315)
  %317 = load double, ptr %33, align 8
  %318 = fadd double %316, %317
  store double %318, ptr %33, align 8
  %319 = load double, ptr %30, align 8
  %320 = load double, ptr %32, align 8
  %321 = load double, ptr %34, align 8
  %322 = load double, ptr %31, align 8
  %323 = fmul double %321, %322
  %324 = call double @llvm.fmuladd.f64(double %319, double %320, double %323)
  %325 = load double, ptr %30, align 8
  %326 = fadd double %324, %325
  store double %326, ptr %30, align 8
  br label %327

327:                                              ; preds = %309
  %328 = load i32, ptr %14, align 4
  %329 = load i32, ptr %11, align 4
  %330 = add nsw i32 %329, %328
  store i32 %330, ptr %11, align 4
  br label %207, !llvm.loop !21

331:                                              ; preds = %207
  %332 = load i32, ptr %18, align 4
  store i32 %332, ptr %17, align 4
  br label %183, !llvm.loop !22

333:                                              ; preds = %183
  %334 = load i32, ptr %23, align 4
  %335 = load i32, ptr %24, align 4
  %336 = mul nsw i32 %335, %334
  store i32 %336, ptr %24, align 4
  br label %337

337:                                              ; preds = %333
  %338 = load i32, ptr %20, align 4
  %339 = add nsw i32 %338, -1
  store i32 %339, ptr %20, align 4
  br label %52, !llvm.loop !23

340:                                              ; preds = %52
  ret void
}

; Function Attrs: nounwind
declare dso_local double @sin(double noundef) #2

; Function Attrs: nocallback nocreateundeforpoison nofree nosync nounwind speculatable willreturn memory(none)
declare double @llvm.fmuladd.f64(double, double, double) #6

attributes #0 = { noinline nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { allocsize(0) "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #2 = { nounwind "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #4 = { noreturn nounwind "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #5 = { nocallback nofree nosync nounwind willreturn memory(argmem: write) }
attributes #6 = { nocallback nocreateundeforpoison nofree nosync nounwind speculatable willreturn memory(none) }
attributes #7 = { allocsize(0) }
attributes #8 = { nounwind }
attributes #9 = { noreturn nounwind }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5}
!llvm.ident = !{!6}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)", isOptimized: false, runtimeVersion: 0, emissionKind: NoDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "E:\\llvm-test-suite\\SingleSource\\Benchmarks\\Misc/ffbench.c", directory: "E:/project")
!2 = !{i32 2, !"Debug Info Version", i32 3}
!3 = !{i32 8, !"PIC Level", i32 2}
!4 = !{i32 7, !"uwtable", i32 2}
!5 = !{i32 1, !"MaxTLSAlign", i32 65536}
!6 = !{!"clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)"}
!7 = distinct !{!7, !8}
!8 = !{!"llvm.loop.mustprogress"}
!9 = distinct !{!9, !8}
!10 = distinct !{!10, !8}
!11 = distinct !{!11, !8}
!12 = distinct !{!12, !8}
!13 = distinct !{!13, !8}
!14 = distinct !{!14, !8}
!15 = distinct !{!15, !8}
!16 = distinct !{!16, !8}
!17 = distinct !{!17, !8}
!18 = distinct !{!18, !8}
!19 = distinct !{!19, !8}
!20 = distinct !{!20, !8}
!21 = distinct !{!21, !8}
!22 = distinct !{!22, !8}
!23 = distinct !{!23, !8}
