class Solution {
    public String longestCommonPrefix(String[] strs) {
    Arrays.sort( strs ) ;
    String str1 = strs[0];
    String str2 = strs[strs.length-1];
    int ind = 0;
    while(ind < str1.length()){
        if(str1.charAt(ind) == str2.charAt(ind)){
            ind++;
        }
        else{
            break;
        }
    } 
    if(ind == 0){
        return "";
    } 
    else{
        return str1.substring(0, ind);
    }
    }
}