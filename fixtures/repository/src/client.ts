import { checkAcl } from './security';
export function loadResource() {
  return checkAcl('read');
}
