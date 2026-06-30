int branch_simplify(int x) {
    int y = 0;
    if (x > 0) {
        y = x;
    } else {
        y = -x;
    }

    if (y >= 0) {
        return y;
    }
    return 0;
}

