import { Toaster as Sonner } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="light"
      richColors
      position="top-right"
      closeButton
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast shadow-[0_12px_40px_rgba(0,0,0,0.35)] border border-zinc-200/90 rounded-xl font-sans",
          title: "font-semibold text-sm text-zinc-900",
          description: "text-xs text-zinc-600 mt-0.5",
          actionButton: "bg-zinc-900 text-white font-medium text-xs",
          cancelButton: "bg-zinc-100 text-zinc-700 font-medium text-xs",
        },
      }}
      {...props}
    />
  );
};

export { Toaster };
