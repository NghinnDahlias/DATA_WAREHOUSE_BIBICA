import {useEffect,useRef} from 'react'
import {createPortal} from 'react-dom'
import {X} from 'lucide-react'

export default function Modal({title,onClose,children,className=''}) {
  const root=useRef(null)
  const close=useRef(onClose)
  close.current=onClose
  useEffect(()=>{
    const previous=document.activeElement
    root.current?.querySelector('button,input,select,[tabindex="0"]')?.focus()
    const key=e=>{
      if(e.key==='Escape'){e.stopImmediatePropagation();close.current();return}
      if(e.key!=='Tab')return
      const nodes=[...root.current.querySelectorAll('button:not(:disabled),input,select,a[href],[tabindex="0"]')].filter(n=>n.getClientRects().length)
      const first=nodes[0],last=nodes.at(-1)
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}
    }
    document.addEventListener('keydown',key,true)
    return ()=>{document.removeEventListener('keydown',key,true);previous?.focus()}
  },[])
  return createPortal(<div className="feature-backdrop" onMouseDown={e=>e.target===e.currentTarget&&onClose()}>
    <section ref={root} className={`feature-dialog ${className}`} role="dialog" aria-modal="true" aria-label={title}>
      <header className="feature-dialog-head"><h2>{title}</h2><button aria-label="Đóng cửa sổ" onClick={onClose}><X size={20}/></button></header>
      <div className="feature-dialog-body">{children}</div>
    </section>
  </div>,document.body)
}
