/*
Structure of a Doubly LinkList
class Node {
    int data;
    Node next;
    Node prev;

    Node(int val) {
        data = val;
        next = null;
        prev = null;
    }
}
*/
class Solution {
    public Node delPos(Node head, int x) {
        // code here
        Node temp = head;
        int cnt = 0;
        while(temp != null){
            cnt++;
            if(cnt == x) break;
            temp = temp.next;
        }
        Node prev = temp.prev;
        Node front = temp.next;
        if(prev == null && front== null){
            return null;
        }else if( prev == null){
            return(deleteHead(head));
        }else if( front == null ){
            return(deleteLastNode(head));
        }else{
            prev.next = front;
            front.prev = prev;
            temp.next = null;
            temp.prev = null;
            return head;
        }
    }
    private Node deleteHead(Node head) {
    if(head == null || head.next== null){
        return null;
    }
    Node prev = head;
    head = head.next;
    head.prev = null;
    prev.next = null;
    return head;
    }
    private Node deleteLastNode(Node head) {
      if(head== null || head.next == null) return null;
      Node tail = head;
      while(tail.next != null){
          tail = tail.next;
      }
      Node prev = tail.prev;
      prev.next = null;
      tail.prev = null;
      return head;
    }
}