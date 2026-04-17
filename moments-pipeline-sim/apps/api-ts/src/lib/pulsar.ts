import Pulsar from "pulsar-client";

let client: Pulsar.Client | null = null;
let producer: Pulsar.Producer | null = null;

export async function getProducer() {
  if (producer) {
    return producer;
  }

  if (!client) {
    client = new Pulsar.Client({
      serviceUrl: process.env.PULSAR_URL ?? "pulsar://127.0.0.1:6650"
    });
  }

  producer = await client.createProducer({
    topic: process.env.TOPIC_MOMENTS_RAW ?? "persistent://public/default/moments.raw"
  });

  return producer;
}
