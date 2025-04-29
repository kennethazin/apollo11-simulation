import EventEmitter from "events";

class WebhookService {
  private static instance: WebhookService;
  private eventEmitter = new EventEmitter();

  // Singleton pattern
  public static getInstance(): WebhookService {
    if (!WebhookService.instance) {
      WebhookService.instance = new WebhookService();
    }
    return WebhookService.instance;
  }

  // Method to handle incoming data
  public handleSpacecraftData(data: { distance: number }): void {
    console.log("Received spacecraft distance data:", data);
    this.eventEmitter.emit("distanceUpdate", data.distance);
  }

  // Subscribe to distance updates
  public onDistanceUpdate(callback: (distance: number) => void): () => void {
    this.eventEmitter.on("distanceUpdate", callback);
    return () => this.eventEmitter.off("distanceUpdate", callback);
  }
}

export default WebhookService;
