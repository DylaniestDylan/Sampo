"use strict";

window.sampoGeneration = function sampoGeneration() {
  return {
    prompt: "",
    generationId: null,
    responseText: "",
    errorText: "",
    status: "idle",
    requestInFlight: false,
    stopping: false,
    eventSource: null,

    get isActive() {
      return this.requestInFlight || this.status === "streaming";
    },

    get canSend() {
      return !this.isActive && this.prompt.trim().length > 0;
    },

    get canStop() {
      return this.status === "streaming" && this.generationId !== null;
    },

    csrfToken() {
      return document.querySelector('meta[name="csrf-token"]').content;
    },

    async responsePayload(response) {
      try {
        return await response.json();
      } catch (_error) {
        return {};
      }
    },

    apiErrorMessage(payload, fallback) {
      if (payload.detail === "model runtime is not configured") {
        return "Local model runtime is unavailable.";
      }
      return typeof payload.detail === "string" ? payload.detail : fallback;
    },

    subscribeToGeneration() {
      if (this.eventSource !== null) {
        this.eventSource.close();
      }
      const generationPath = encodeURIComponent(this.generationId);
      this.eventSource = new EventSource(
        `/api/generations/${generationPath}/events`,
      );
      this.eventSource.addEventListener("generation.started", () => {
        this.status = "streaming";
      });
      this.eventSource.addEventListener("generation.delta", (event) => {
        const payload = this.eventPayload(event);
        if (payload !== null && typeof payload.text === "string") {
          this.responseText += payload.text;
        }
      });
      this.eventSource.addEventListener("generation.completed", () => {
        this.finish("completed");
      });
      this.eventSource.addEventListener("generation.stopped", () => {
        this.finish("stopped");
      });
      this.eventSource.addEventListener("generation.failed", (event) => {
        const payload = this.eventPayload(event);
        this.finish(
          "failed",
          payload !== null && typeof payload.error === "string"
            ? payload.error
            : "Generation failed.",
        );
      });
      this.eventSource.onerror = () => {
        if (this.status === "streaming") {
          this.finish("failed", "Generation stream disconnected.");
        }
      };
    },

    eventPayload(event) {
      try {
        const payload = JSON.parse(event.data);
        return payload !== null && typeof payload === "object" ? payload : null;
      } catch (_error) {
        return null;
      }
    },

    finish(status, errorText = "") {
      this.status = status;
      this.errorText = errorText;
      this.stopping = false;
      if (this.eventSource !== null) {
        this.eventSource.close();
        this.eventSource = null;
      }
    },

    async stopGeneration() {
      if (!this.canStop || this.stopping) {
        return;
      }
      this.stopping = true;
      const generationPath = encodeURIComponent(this.generationId);
      try {
        const response = await fetch(
          `/api/generations/${generationPath}/cancel`,
          {
            method: "POST",
            credentials: "same-origin",
            headers: { "X-CSRF-Token": this.csrfToken() },
          },
        );
        const payload = await this.responsePayload(response);
        if (!response.ok || typeof payload.status !== "string") {
          this.finish(
            "failed",
            this.apiErrorMessage(payload, "Generation could not be stopped."),
          );
          return;
        }
        this.finish(
          payload.status,
          typeof payload.error === "string" ? payload.error : "",
        );
      } catch (_error) {
        this.finish("failed", "Sampo could not stop the generation.");
      } finally {
        this.stopping = false;
      }
    },

    async send() {
      if (!this.canSend) {
        return;
      }
      this.requestInFlight = true;
      this.responseText = "";
      this.errorText = "";
      this.status = "idle";
      this.generationId = null;
      try {
        const response = await fetch("/api/generations", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": this.csrfToken(),
          },
          body: JSON.stringify({ prompt: this.prompt }),
        });
        const payload = await this.responsePayload(response);
        if (!response.ok || typeof payload.generation_id !== "string") {
          this.status = "failed";
          this.errorText = this.apiErrorMessage(
            payload,
            "Generation could not be started.",
          );
          return;
        }
        this.generationId = payload.generation_id;
        this.status = "streaming";
        this.subscribeToGeneration();
      } catch (_error) {
        this.status = "failed";
        this.errorText = "Sampo could not start the generation.";
      } finally {
        this.requestInFlight = false;
      }
    },
  };
};
