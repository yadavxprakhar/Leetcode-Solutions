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
    public ListNode removeNthFromEnd(ListNode head, int n) {

        int len = lengthLL(head);
        if (n == len) {
            return head.next;
        }
        int k = len - n; 
        ListNode temp = head;
        for (int i = 1; i < k; i++) {
            temp = temp.next;
        }
        temp.next = temp.next.next;
        return head;
    }

    private int lengthLL(ListNode head) {
        int cnt = 0;
        while (head != null) {
            cnt++;
            head = head.next;
        }
        return cnt;
    }
}