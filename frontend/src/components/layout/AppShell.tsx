"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { usePathname } from "next/navigation";
import { TopNav } from "./TopNav";
import { Sidebar } from "./Sidebar";
import { Menu, X } from "lucide-react";

const PAGE_ANIMATION = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 },
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen flex-col bg-[linear-gradient(180deg,rgba(248,250,252,1),rgba(241,245,249,0.94))]">
      <TopNav onMenuClick={() => setSidebarOpen((v) => !v)} />
      <div className="flex flex-1 overflow-hidden">
        {/* Desktop sidebar */}
        <div className="hidden lg:block">
          <Sidebar />
        </div>

        {/* Mobile sidebar overlay */}
        <AnimatePresence>
          {sidebarOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-40 bg-black/40 lg:hidden"
                onClick={() => setSidebarOpen(false)}
              />
              <motion.div
                initial={{ x: -280 }}
                animate={{ x: 0 }}
                exit={{ x: -280 }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="fixed bottom-0 left-0 top-0 z-50 lg:hidden"
              >
                <div className="relative h-full">
                  <button
                    onClick={() => setSidebarOpen(false)}
                    className="absolute right-3 top-3 z-10 rounded-lg p-1 text-[var(--muted)] hover:bg-[var(--panel-soft)]"
                  >
                    <X size={20} />
                  </button>
                  <Sidebar />
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial="initial"
              animate="animate"
              exit="exit"
              variants={PAGE_ANIMATION}
              transition={{ duration: 0.2, ease: "easeOut" }}
            >
              <div className="rounded-[2rem] border border-white/60 bg-[linear-gradient(180deg,rgba(255,255,255,0.9),rgba(248,250,252,0.9))] p-4 shadow-[0_18px_60px_rgba(15,23,42,0.05)] md:p-6">
                {children}
              </div>
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
