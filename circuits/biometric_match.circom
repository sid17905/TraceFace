pragma circom 2.1.0;

template GreaterEqThan(n) {
    signal input in[2];
    signal output out;

    signal diff;
    diff <-- in[0] - in[1];

    signal isNeg;
    isNeg <-- (in[0] < in[1]) ? 1 : 0;
    out <-- 1 - isNeg;
}

template BiometricMatch(N) {
    signal input queryEmbedding[N];
    signal input ledgerEmbedding[N];
    signal input threshold;
    
    signal output isValidMatch;
    signal output dotProduct;

    signal products[N];
    signal runningSum[N];

    products[0] <== queryEmbedding[0] * ledgerEmbedding[0];
    runningSum[0] <== products[0];

    for (var i = 1; i < N; i++) {
        products[i] <== queryEmbedding[i] * ledgerEmbedding[i];
        runningSum[i] <== runningSum[i - 1] + products[i];
    }

    dotProduct <== runningSum[N - 1];

    component gte = GreaterEqThan(64);
    gte.in[0] <== dotProduct;
    gte.in[1] <== threshold;

    isValidMatch <== gte.out;
}

component main {public [threshold]} = BiometricMatch(512);
