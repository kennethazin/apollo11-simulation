class WebSocketService {
  private static instance: WebSocketService;
  private socket: WebSocket | null = null;
  private callbacks: Map<string, ((data: any) => void)[]> = new Map();

  private constructor() {
    this.connect();
  }

  public static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  private connect(): void {
    // Connect to WebSocket server (adjust URL as needed)
    this.socket = new WebSocket("ws://localhost:3001/ws");

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type && this.callbacks.has(data.type)) {
          this.callbacks
            .get(data.type)
            ?.forEach((callback) => callback(data.payload));
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    this.socket.onclose = () => {
      console.log("WebSocket connection closed. Reconnecting...");
      setTimeout(() => this.connect(), 2000);
    };
  }

  public subscribe(type: string, callback: (data: any) => void): () => void {
    if (!this.callbacks.has(type)) {
      this.callbacks.set(type, []);
    }
    this.callbacks.get(type)?.push(callback);

    return () => {
      const callbacks = this.callbacks.get(type);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index !== -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }
}

export default WebSocketService;
