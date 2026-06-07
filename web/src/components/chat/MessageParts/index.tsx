import type { UIMessagePart, UIDataTypes, UITools } from 'ai';
import { TextPart } from './TextPart';

interface Props {
  part: UIMessagePart<UIDataTypes, UITools>;
}

/**
 * Dispatches a single message part to its renderer based on `part.type`.
 * Future tool/file/image parts plug in here without touching MessageItem.
 */
export function MessagePartView({ part }: Props) {
  switch (part.type) {
    case 'text':
      return <TextPart text={part.text} />;
    default:
      return null;
  }
}
