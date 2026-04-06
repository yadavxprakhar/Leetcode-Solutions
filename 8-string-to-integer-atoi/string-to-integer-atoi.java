class Solution {
    public int myAtoi(String s) {
    s= s.trim();
    long nums=0;
    if(s.isEmpty()){
        return 0;
    } 
    int i=0;
    int sign=1;
    int n = s.length();
    if(s.charAt(i)=='-' || s.charAt(i)=='+')  {
        sign= (s.charAt(i)=='-')?-1:1;
        i++;
    } 
    while (i<n && Character.isDigit(s.charAt(i))){
        nums=nums*10+(s.charAt(i)-'0');
        if(nums*sign >Integer.MAX_VALUE){
            return Integer.MAX_VALUE;
        }
        if(nums*sign < Integer.MIN_VALUE){
            return Integer.MIN_VALUE;
        }
        i++;
    }
    return (int) (sign*nums);
    }
}