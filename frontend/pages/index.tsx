import { useMemo, useState } from "react";
import styles from "../styles/Home.module.css";

export default function Home() {
  const [name, setName] = useState("");
  const [feeling, setFeeling] = useState("");
  const [details, setDetails] = useState("");
  const [affirmation, setAffirmation] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const apiBaseUrl = useMemo(() => {
    return (
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"
    ).replace(/\/$/, "");
  }, []);

  const feelingPresets = [
    "Grounded",
    "Anxious",
    "Overwhelmed",
    "Hopeful",
    "Lonely",
    "Motivated",
    "Restless",
    "Tender",
  ];

  async function handleGenerate() {
    if (!name.trim() || !feeling.trim()) {
      setError("Please add your name and how you're feeling.");
      return;
    }

    setLoading(true);
    setError("");
    setAffirmation("");

    try {
      const res = await fetch(`${apiBaseUrl}/api/affirmation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, feeling, details }),
      });

      if (!res.ok) {
        throw new Error("Failed to fetch affirmation");
      }

      const data = await res.json();
      setAffirmation(data.affirmation);
    } catch {
      setError(
        "We hit a small snag. Please try again in a moment, or adjust your input."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.glow} aria-hidden="true" />
      <main className={styles.card}>
        <header className={styles.header}>
          <p className={styles.kicker}>Live Mood Architect</p>
          <h1 className={styles.title}>
            A gentle, personalized affirmation in under a minute.
          </h1>
          <p className={styles.subtitle}>
            Share your name, how you feel, and any context. We'll craft a short,
            supportive affirmation grounded in your moment.
          </p>
        </header>

        <section className={styles.form}>
          <label className={styles.field}>
            <span>Your name</span>
            <input
              placeholder="e.g. Amina"
              value={name}
              onChange={e => setName(e.target.value)}
              autoComplete="name"
            />
          </label>
          <label className={styles.field}>
            <span>How are you feeling?</span>
            <input
              placeholder="e.g. Overwhelmed but hopeful"
              value={feeling}
              onChange={e => setFeeling(e.target.value)}
            />
            <ul className={styles.chipRow}>
              {feelingPresets.map(preset => (
                <li key={preset}>
                  <button
                    type="button"
                    className={`${styles.chip} ${
                      feeling.toLowerCase() === preset.toLowerCase()
                        ? styles.chipActive
                        : ""
                    }`}
                    onClick={() => setFeeling(preset)}
                  >
                    {preset}
                  </button>
                </li>
              ))}
            </ul>
          </label>
          <label className={styles.field}>
            <span>Details (optional)</span>
            <textarea
              placeholder="Anything you'd like the affirmation to reflect"
              value={details}
              onChange={e => setDetails(e.target.value)}
              rows={3}
            />
          </label>
        </section>

        <div className={styles.actions}>
          <button
            className={styles.button}
            onClick={handleGenerate}
            disabled={loading}
          >
            {loading ? "Crafting..." : "Generate affirmation"}
          </button>
          <p className={styles.hint}>
            We keep this short and supportive—no clinical advice.
          </p>
        </div>

        <section className={styles.result} aria-live="polite">
          {loading && <div className={styles.loader} />}
          {error && <p className={styles.error}>{error}</p>}
          {!loading && !error && affirmation && (
            <p className={styles.affirmation}>{affirmation}</p>
          )}
        </section>
      </main>
    </div>
  );
}
