
import React, {useState, useEffect} from 'react'
import axios from 'axios'

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [viewer, setViewer] = useState(null)

  const send = async () => {
    if (!input) return
    const userMsg = { role: 'user', text: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    try {
      const resp = await axios.post('/api/chat/query', { query: input, user_id: 1 })
      const data = resp.data
      const assistantMsg = { role: 'assistant', text: 'Plan: ' + JSON.stringify(data.plan), task_id: data.task_id }
      setMessages(prev => [...prev, assistantMsg])
      if (data.task_id) {
        pollTask(data.task_id)
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Error: ' + e.message }])
    }
  }

  const pollTask = async (task_id) => {
    setMessages(prev => [...prev, { role:'system', text: 'Task queued: ' + task_id }])
    let attempts = 0
    while (attempts < 60) {
      try {
        const r = await axios.get('/api/tasks/' + task_id)
        if (r.data.status === 'ok' && r.data.db && r.data.db.result) {
          const res = r.data.db.result
          let text = 'Task finished: ' + JSON.stringify(res)
          setMessages(prev => [...prev, { role:'assistant', text }])
          // if result contains artifacts, display thumbnails
          try {
            let parsed = res
            if (typeof parsed === 'string') parsed = JSON.parse(parsed)
            const artifacts = parsed.artifacts || parsed.artifacts || parsed.artifacts
            if (artifacts && artifacts.screenshot) {
              const url = '/api/artifacts/' + artifacts.screenshot.split('/').pop()
              setMessages(prev => [...prev, { role:'assistant', text: 'Screenshot:', img: url }])
            }
          } catch (e) {}
          return
        }
      } catch (e) {
        // ignore and retry
      }
      await new Promise(r => setTimeout(r, 2000))
      attempts += 1
    }
    setMessages(prev => [...prev, { role:'assistant', text: 'Task poll timeout' }])
  }

  return (
    <div style={{padding:20, maxWidth:900, margin:'0 auto'}}>
      <h2>Ecomm Chat</h2>
      <div style={{border:'1px solid #ddd', padding:10, minHeight:240}}>
        {messages.map((m,i) => <div key={i} style={{margin:'8px 0'}}>
          <b>{m.role}:</b> {m.text} {m.img && <img src={m.img} style={{maxWidth:200, cursor:'pointer'}} onClick={()=>setViewer(m.img)} />}
        </div>)}
      </div>
      <div style={{marginTop:10}}>
        <input value={input} onChange={e=>setInput(e.target.value)} style={{width:'70%'}} />
        <button onClick={send} style={{marginLeft:8}}>Send</button>
      </div>
      {viewer && (
        <div style={{position:'fixed', left:0, top:0, right:0, bottom:0, background:'rgba(0,0,0,0.6)', display:'flex', alignItems:'center', justifyContent:'center'}} onClick={()=>setViewer(null)}>
          <img src={viewer} style={{maxWidth:'90%', maxHeight:'90%'}} />
        </div>
      )}
    </div>
  )
}
