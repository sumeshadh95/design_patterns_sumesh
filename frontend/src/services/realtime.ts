// Phase 11 stub. Phase 12 replaces this body with the dashboard WebSocket,
// which subscribes to the backend EventBus and pushes events here.

export type RealtimeEvent = {
  type: string;
  payload: unknown;
};

export function subscribeRealtime(
  onEvent: (event: RealtimeEvent) => void,
): () => void {
  // No socket yet: nothing is ever delivered. The Event feed polls instead.
  void onEvent;

  return () => {};
}
