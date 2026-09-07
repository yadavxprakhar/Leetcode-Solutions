class Solution {
    int M = 1000000007;
    int[] dp = new int[2001];
    int[] prev; 
    public int distinctSubseqII(String s) {
        int n = s.length();
        Arrays.fill(dp, -1);
        prev = new int[n+1];
        int[] lastSeen = new int[26];
        for(int i = 1; i <= n; i++) {
            int idx = s.charAt(i-1) - 'a';
            prev[i] = lastSeen[idx];
            lastSeen[idx] = i;
        }
        dp[0] = 1;
        for(int i = 1; i <= n; i++) {
            int total = (int)(2L * dp[i-1] % M);
            if(prev[i] != 0) {
                int duplicates = dp[prev[i] - 1];
                total = (total - duplicates + M) % M;
            }
            dp[i] = total;
        }
        return (dp[n] - 1 + M) % M;
    }
}