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
        style: {
          background: "#ffffff",
          color: "#09090b",
          border: "1px solid #e4e4e7",
          boxShadow: "0 20px 45px -10px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(0, 0, 0, 0.08)",
        },
        classNames: {
          toast:
            "!bg-white !text-zinc-900 shadow-[0_20px_45px_-10px_rgba(0,0,0,0.6)] border border-zinc-200 rounded-xl font-sans",
          title: "!text-zinc-900 font-bold text-sm",
          description: "!text-zinc-600 text-xs mt-0.5",
          actionButton: "!bg-zinc-900 !text-white font-medium text-xs",
          cancelButton: "!bg-zinc-100 !text-zinc-700 font-medium text-xs",
          closeButton: "!bg-white !text-zinc-600 !border-zinc-200 hover:!bg-zinc-100 hover:!text-zinc-900",
        },
      }}
      {...props}
    />
  );
};

export { Toaster };
