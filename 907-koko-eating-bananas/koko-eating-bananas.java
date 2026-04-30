class Solution {
    public int minEatingSpeed(int[] piles, int h) {
    int low = 1;
    int high = findMax( piles);
    while(low <= high){
        int mid = (low+high)/2;
        long totalHour = totalHours(piles, mid);
        if( totalHour <= h){
            high = mid-1;
        }
        else{
            low = mid+1;
        }
    }
    return low;
    }
    private int findMax(int[] piles ) {
        int max1 = Integer.MIN_VALUE;
        int n = piles.length;
        for(int i= 0; i<n; i++){
            max1 = Math.max( max1, piles[i]);
        }  
    return max1;  
    }

    private long totalHours( int[] piles, int hourly){
        long totalHour = 0;
        int n = piles.length;
        for(int i=0; i<n; i++ ){
            totalHour += (piles[i] + hourly - 1) / hourly;
        }
    return totalHour;
    }
    
}