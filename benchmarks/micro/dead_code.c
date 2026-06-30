int dead_code(int x) {
    int a = x + 1;
    int b = a * 2;
    int c = b - b;
    return x + c;
}

