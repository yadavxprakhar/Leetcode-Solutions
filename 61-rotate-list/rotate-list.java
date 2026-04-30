/**
 * Definition for singly-linked list.
 * public class ListNode {
 *     int val;
 *     ListNode next;
 *     ListNode() {}
 *     ListNode(int val) { this.val = val; }
 *     ListNode(int val, ListNode next) { this.val = val; this.next = next; }
 * }
 */
class Solution {
    public ListNode rotateRight(ListNode head, int k) {
    if(head == null || k == 0) return head;    
    ListNode tail = head;
    int len = 1;
    while(tail.next != null){
        len++;
        tail = tail.next;
    } 
    if( k % len == 0)   return head;
    k = k%len;
    tail.next = head;
    ListNode node1 = kthNode(head, len-k);
    head = node1.next;
    node1.next = null;
    return head;
    }
    private ListNode kthNode(ListNode head, int k){
        int cnt = 0;
        ListNode temp = head;
        while(temp != null){
            cnt++;
            if(cnt == k){
                break;
            }
            temp = temp.next;
        }
        return temp;
    }
}