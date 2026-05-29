interface ErrorStateProps {
  title?: string;
  message: string;
}

export function ErrorState({ title = "Something went wrong", message }: ErrorStateProps) {
  return (
    <div className="error-state">
      <strong>{title}</strong>
      <p>{message}</p>
    </div>
  );
}
