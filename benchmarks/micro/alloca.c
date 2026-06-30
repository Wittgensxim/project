int alloca_sroa(int x) {
    int pair[2];
    pair[0] = x;
    pair[1] = x + 1;
    return pair[0] + pair[1];
}

