class Solution {
    public int numDistinct(String s, String t) {
        int m = s.length();
        int n = t.length();

        long[] curr = new long[n+1];
        long[] prev = new long[n+1];
        
        prev[0] = curr[0] = 1;
        
        for(int i = 1; i<m+1; i++) {
            
            for(int j = 1; j<n+1; j++) {
                
                if(s.charAt(i-1) == t.charAt(j-1))
                    curr[j] = prev[j-1] + prev[j];
                else
                    curr[j] = prev[j];
            }
            prev = curr.clone();
        }
        return (int) prev[n];
    }
}