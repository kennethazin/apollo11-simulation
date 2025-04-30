"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";

export default function SpaceLoadingScreen() {
  const [progress, setProgress] = useState(0);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  // Loading messages
  const loadingMessages = [
    "Initialising systems",
    "Checking life support",
    "Calculating orbital trajectories",
    "Fueling thrusters",
    "Calibrating navigation systems",
  ];

  // Simulate loading progress
  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsComplete(true);
          return 100;
        }

        // Update message based on progress
        const newIndex = Math.min(
          Math.floor((prev / 100) * loadingMessages.length),
          loadingMessages.length - 1
        );

        if (newIndex !== currentMessageIndex) {
          setCurrentMessageIndex(newIndex);
        }

        return prev + 0.71; // Adjusted to complete in 7 seconds
      });
    }, 50);

    // Ensure loading completes in exactly 7 seconds
    const timeout = setTimeout(() => {
      setProgress(100);
      setIsComplete(true);
    }, 7000);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [currentMessageIndex]);

  return (
    <div className="relative h-screen w-full bg-zinc-950 overflow-hidden flex flex-col items-center justify-center px-4">
      <div className="absolute inset-0">
        {[...Array(40)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full bg-white"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
              opacity: Math.random() * 0.3 + 0.1,
            }}
            animate={{
              opacity: [null, 0.1, 0.3, 0.1],
            }}
            transition={{
              duration: Math.random() * 4 + 3,
              repeat: Number.POSITIVE_INFINITY,
              ease: "easeInOut",
            }}
            style={{
              width: `${Math.random() * 2 + 1}px`,
              height: `${Math.random() * 2 + 1}px`,
            }}
          />
        ))}
      </div>

      <motion.div
        className="text-zinc-400 text-sm font-light tracking-wider mb-12 h-5 overflow-hidden"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 0.2 }}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={isComplete ? "ready" : currentMessageIndex}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -20, opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="uppercase text-center"
          >
            {isComplete ? "READY" : loadingMessages[currentMessageIndex]}
          </motion.div>
        </AnimatePresence>
      </motion.div>

      {/* Minimal progress bar */}
      <div className="w-64 h-[1px] bg-zinc-800 relative overflow-hidden">
        <motion.div
          className="h-full bg-zinc-400"
          initial={{ width: "0%" }}
          animate={{ width: `${progress}%` }}
          transition={{ ease: "easeInOut" }}
        />
      </div>

      <motion.div
        className="absolute top-1/2 left-1/2 w-48 h-48 border border-zinc-800 rounded-full"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.3, scale: [0.8, 1.2, 0.8] }}
        transition={{
          duration: 15,
          repeat: Number.POSITIVE_INFINITY,
          ease: "easeInOut",
        }}
        style={{ transform: "translate(-50%, -50%)" }}
      />

      <motion.div
        className="absolute top-1/2 left-1/2 w-72 h-72 border border-zinc-900 rounded-full"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.2, scale: [1, 1.3, 1] }}
        transition={{
          duration: 20,
          repeat: Number.POSITIVE_INFINITY,
          ease: "easeInOut",
          delay: 2,
        }}
        style={{ transform: "translate(-50%, -50%)" }}
      />
    </div>
  );
}
