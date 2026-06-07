interface Props {
  text: string;
}

export function TextPart({ text }: Props) {
  return <div className="whitespace-pre-wrap break-words">{text}</div>;
}
