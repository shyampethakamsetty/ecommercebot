
import React, {useState, useEffect} from 'react'
import axios from 'axios'

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [viewer, setViewer] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const send = async () => {
    if (!input.trim()) return
    const userMsg = { role: 'user', text: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsLoading(true)
    
    try {
      const resp = await axios.post('/api/chat/query', { query: input, user_id: 1 })
      const data = resp.data
      
      // Handle different response statuses
      if (data.status === 'needs_credentials') {
        const assistantMsg = { role: 'assistant', text: data.message || 'Please provide your login credentials to proceed with checkout.' }
        setMessages(prev => [...prev, assistantMsg])
        setIsLoading(false)
        return
      }
      
      const assistantMsg = { role: 'assistant', text: 'Plan: ' + JSON.stringify(data.plan), task_id: data.task_id }
      setMessages(prev => [...prev, assistantMsg])
      if (data.task_id) {
        pollTask(data.task_id)
      } else {
        setIsLoading(false)
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Error: ' + e.message }])
      setIsLoading(false)
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
            
            // Handle multiple screenshots from enhanced workflow
            const artifacts = parsed.artifacts
            if (artifacts && Array.isArray(artifacts)) {
              // Multiple screenshots - display each with context
              artifacts.forEach((artifact, index) => {
                if (artifact && artifact.screenshot) {
                  const filename = artifact.screenshot.split('/').pop()
                  const url = '/api/artifacts/' + filename
                  
                  // Determine screenshot context from filename
                  console.log('Processing screenshot:', filename)
                  
                  const getScreenshotContext = (filename) => {
                    if (filename.includes('login-page-loaded')) return '🔐 Login Page Loaded'
                    if (filename.includes('login-credentials-filled')) return '📝 Credentials Entered'
                    if (filename.includes('login-landing-page')) return '✅ Successfully Logged In'
                    if (filename.includes('search-results-page')) return '🔍 Search Results'
                    if (filename.includes('search-filter-applied')) return '🎯 Price Filter Applied'
                    if (filename.includes('cart-product-added')) return '🛒 Product Added to Cart'
                    if (filename.includes('cart-no-products')) return '🔍 No Products Found'
                    if (filename.includes('cart-before-adding-all')) return '🛒 Cart Before Adding Products'
                    if (filename.includes('cart-after-adding-all')) return '📦 Products Added to Cart'
                    if (filename.includes('cart-cart-with-all-products')) return '🛍️ Cart with All Products'
                    if (filename.includes('cart-add-all-error')) return '❌ Error Adding Products to Cart'
                    if (filename.includes('checkout-billing-address')) return '📝 Step 1: Billing Address'
                    if (filename.includes('checkout-shipping-address')) return '📦 Step 2: Shipping Address'
                    if (filename.includes('checkout-shipping-method')) return '🚚 Step 3: Shipping Method'
                    if (filename.includes('checkout-payment-method')) return '💳 Step 4: Payment Method'
                    if (filename.includes('checkout-payment-info')) return 'ℹ️ Step 5: Payment Information'
                    if (filename.includes('checkout-confirm-order')) return '✅ Step 6: Confirm Order'
                                         if (filename.includes('checkout-thank-you-page')) return '🎉 Thank You - Order Complete!'
                     if (filename.includes('checkout-order-processing-fallback')) return '⚠️ Order Processing (Debug)'
                     if (filename.includes('checkout-order-complete')) return '🎉 Order Complete!'
                    if (filename.includes('checkout-cart-page')) return '💳 Checkout - Cart Review'
                    if (filename.includes('checkout-checkout-page')) return '🎉 Checkout - Order Complete'
                    if (filename.includes('addtocart')) return '➕ Added to Cart'
                    if (filename.includes('checkout')) return '💰 Checkout Process'
                    
                    // Fallback - show filename for debugging
                    return `Screenshot (${filename})`
                  }
                  
                  const context = getScreenshotContext(filename)
                  console.log('Final context for', filename, ':', context)
                  
                  const displayText = context
                  
                  setMessages(prev => [...prev, { 
                    role:'assistant', 
                    text: displayText, 
                    img: url 
                  }])
                }
              })
              
              // Add summary message
              const totalScreenshots = parsed.total_screenshots || artifacts.length
              setMessages(prev => [...prev, { 
                role:'assistant', 
                text: `Workflow completed with ${totalScreenshots} screenshots captured.`
              }])
              
            } else if (artifacts && artifacts.screenshot) {
              // Legacy single screenshot handling
              const url = '/api/artifacts/' + artifacts.screenshot.split('/').pop()
              setMessages(prev => [...prev, { role:'assistant', text: 'Screenshot:', img: url }])
            }
          } catch (e) {}
          setIsLoading(false)
          return
        }
      } catch (e) {
        // ignore and retry
      }
      await new Promise(r => setTimeout(r, 2000))
      attempts += 1
    }
    setMessages(prev => [...prev, { role:'assistant', text: 'Task poll timeout' }])
    setIsLoading(false)
  }

  return (
    <>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        fontFamily: '"Inter", "Segoe UI", "Roboto", sans-serif'
      }}>
      {/* Header */}
      <div style={{
        background: 'rgba(255,255,255,0.95)',
        backdropFilter: 'blur(10px)',
        padding: '20px 0',
        borderBottom: '1px solid rgba(255,255,255,0.2)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
      }}>
        <div style={{maxWidth: 1000, margin: '0 auto', padding: '0 20px'}}>
          <h1 style={{
            margin: 0,
            fontSize: '2.2rem',
            fontWeight: '700',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            textAlign: 'center'
          }}>
            🛒 demo.nopcommerce AI Assistant
          </h1>
          <p style={{
            margin: '8px 0 0 0',
            textAlign: 'center',
            color: '#666',
            fontSize: '1.1rem'
          }}>
            AI-powered shopping assistant for nopCommerce demo store
          </p>
        </div>
      </div>

      {/* Main Chat Container */}
      <div style={{maxWidth: 1000, margin: '0 auto', padding: '30px 20px'}}>
        
        {/* Messages Container */}
        <div style={{
          background: 'rgba(255,255,255,0.95)',
          backdropFilter: 'blur(10px)',
          borderRadius: '20px',
          padding: '30px',
          minHeight: '500px',
          maxHeight: '70vh',
          overflowY: 'auto',
          boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
          border: '1px solid rgba(255,255,255,0.3)'
        }}>
          {messages.length === 0 && (
            <div style={{
              textAlign: 'center',
              color: '#555',
              fontSize: '1rem',
              marginTop: '40px',
              padding: '20px',
              background: 'linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%)',
              borderRadius: '15px',
              border: '2px solid rgba(102,126,234,0.2)'
            }}>
              <div style={{fontSize: '3rem', marginBottom: '20px'}}>🛒</div>
              <div style={{fontSize: '1.3rem', fontWeight: '600', marginBottom: '15px', color: '#333'}}>
                Welcome to the AI Shopping Assistant!
              </div>
              
              <div style={{textAlign: 'left', marginTop: '20px', lineHeight: '1.6'}}>
                <div style={{marginBottom: '15px', padding: '10px', background: 'rgba(255,255,255,0.7)', borderRadius: '8px'}}>
                  <strong>📝 Step 1: Register an Account</strong><br/>
                  Go to <a href="https://demo.nopcommerce.com/register" target="_blank" style={{color: '#667eea', textDecoration: 'underline'}}>https://demo.nopcommerce.com/register</a> and create an account.
                </div>
                
                <div style={{marginBottom: '15px', padding: '10px', background: 'rgba(255,255,255,0.7)', borderRadius: '8px'}}>
                  <strong>📍 Step 2: Add a Saved Address</strong><br/>
                  After registration, make sure to add a saved billing/shipping address in your account settings.
                </div>
                
                <div style={{marginBottom: '15px', padding: '10px', background: 'rgba(255,255,255,0.7)', borderRadius: '8px'}}>
                  <strong>💬 Step 3: Start Shopping!</strong><br/>
                  Type your request in natural language with your credentials:
                </div>
                
                <div style={{marginTop: '15px', fontSize: '0.9rem'}}>
                  <div style={{fontWeight: '600', marginBottom: '8px'}}>Example Commands:</div>
                  <div style={{fontFamily: 'monospace', background: 'rgba(0,0,0,0.05)', padding: '8px', borderRadius: '5px', marginBottom: '5px'}}>
                    "buy me books under 50 bucks user: your@email.com pass: yourpassword"
                  </div>
                  <div style={{fontFamily: 'monospace', background: 'rgba(0,0,0,0.05)', padding: '8px', borderRadius: '5px', marginBottom: '5px'}}>
                    "add to cart mobile above 500 dollars user: your@email.com pass: yourpassword"
                  </div>
                  <div style={{fontFamily: 'monospace', background: 'rgba(0,0,0,0.05)', padding: '8px', borderRadius: '5px'}}>
                    "search for laptops and checkout user: your@email.com pass: yourpassword"
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {messages.map((m,i) => (
            <div key={i} style={{
              margin: '20px 0',
              display: 'flex',
              flexDirection: m.role === 'user' ? 'row-reverse' : 'row',
              alignItems: 'flex-start',
              gap: '12px'
            }}>
              {/* Avatar */}
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: m.role === 'user' 
                  ? 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
                  : 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.2rem',
                color: 'white',
                fontWeight: 'bold',
                flexShrink: 0
              }}>
                {m.role === 'user' ? '👤' : '🤖'}
              </div>
              
              {/* Message Bubble */}
              <div style={{
                maxWidth: '70%',
                background: m.role === 'user' 
                  ? 'rgba(255,255,255,1)'
                  : 'rgba(248,249,250,1)',
                color: m.role === 'user' ? '#333' : '#333',
                padding: '16px 20px',
                borderRadius: m.role === 'user' ? '20px 20px 5px 20px' : '20px 20px 20px 5px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
                border: m.role === 'user' 
                  ? '2px solid rgba(102,126,234,0.3)' 
                  : '1px solid rgba(0,0,0,0.05)',
                fontSize: '1rem',
                lineHeight: '1.5'
              }}>
                <div>{m.text}</div>
                
                {/* Screenshot */}
                {m.img && (
                  <div style={{marginTop: '12px'}}>
                    <img 
                      src={m.img} 
                      style={{
                        maxWidth: '100%',
                        height: 'auto',
                        borderRadius: '12px',
                        cursor: 'pointer',
                        boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
                        transition: 'transform 0.2s ease'
                      }}
                      onClick={() => setViewer(m.img)}
                      onMouseEnter={(e) => e.target.style.transform = 'scale(1.02)'}
                      onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
                    />
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {/* Loading Spinner */}
          {isLoading && (
            <div style={{
              margin: '20px 0',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px'
            }}>
              {/* AI Avatar */}
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.2rem',
                color: 'white',
                fontWeight: 'bold',
                flexShrink: 0
              }}>
                🤖
              </div>
              
              {/* Loading Message Bubble */}
              <div style={{
                maxWidth: '70%',
                background: 'rgba(248,249,250,1)',
                color: '#333',
                padding: '16px 20px',
                borderRadius: '20px 20px 20px 5px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
                border: '1px solid rgba(0,0,0,0.05)',
                fontSize: '1rem',
                lineHeight: '1.5',
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
              }}>
                {/* Animated Spinner */}
                <div style={{
                  width: '20px',
                  height: '20px',
                  border: '2px solid #f3f3f3',
                  borderTop: '2px solid #667eea',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
                <span>Processing your request...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input Container */}
        <div style={{
          background: 'rgba(255,255,255,0.95)',
          backdropFilter: 'blur(10px)',
          borderRadius: '20px',
          padding: '20px',
          marginTop: '20px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
          border: '1px solid rgba(255,255,255,0.3)'
        }}>
          <div style={{display: 'flex', gap: '15px', alignItems: 'center'}}>
            <input 
              value={input} 
              onChange={e => setInput(e.target.value)}
              onKeyPress={e => e.key === 'Enter' && !isLoading && send()}
              placeholder={isLoading ? "Processing..." : "Ask me to buy something or search for products..."}
              disabled={isLoading}
              style={{
                flex: 1,
                padding: '16px 20px',
                borderRadius: '15px',
                border: '2px solid rgba(102,126,234,0.2)',
                fontSize: '1rem',
                outline: 'none',
                transition: 'all 0.3s ease',
                background: isLoading ? '#f5f5f5' : 'white',
                opacity: isLoading ? 0.7 : 1,
                cursor: isLoading ? 'not-allowed' : 'text'
              }}
              onFocus={(e) => !isLoading && (e.target.style.borderColor = '#667eea')}
              onBlur={(e) => !isLoading && (e.target.style.borderColor = 'rgba(102,126,234,0.2)')}
            />
            <button 
              onClick={() => !isLoading && send()}
              disabled={isLoading}
              style={{
                padding: '16px 24px',
                borderRadius: '15px',
                border: 'none',
                background: isLoading 
                  ? 'linear-gradient(135deg, #ccc 0%, #999 100%)'
                  : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: isLoading 
                  ? '0 2px 8px rgba(0,0,0,0.1)'
                  : '0 4px 15px rgba(102,126,234,0.3)',
                opacity: isLoading ? 0.7 : 1
              }}
              onMouseEnter={(e) => {
                if (!isLoading) {
                  e.target.style.transform = 'translateY(-2px)'
                  e.target.style.boxShadow = '0 6px 20px rgba(102,126,234,0.4)'
                }
              }}
              onMouseLeave={(e) => {
                if (!isLoading) {
                  e.target.style.transform = 'translateY(0)'
                  e.target.style.boxShadow = '0 4px 15px rgba(102,126,234,0.3)'
                }
              }}
            >
              {isLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '14px',
                    height: '14px',
                    border: '2px solid transparent',
                    borderTop: '2px solid white',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                  Processing...
                </div>
              ) : (
                'Send ✨'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Image Viewer Modal */}
      {viewer && (
        <div 
          style={{
            position: 'fixed', 
            left: 0, 
            top: 0, 
            right: 0, 
            bottom: 0, 
            background: 'rgba(0,0,0,0.9)',
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            zIndex: 1000,
            backdropFilter: 'blur(5px)'
          }} 
          onClick={() => setViewer(null)}
        >
          <div style={{
            position: 'relative',
            maxWidth: '95%',
            maxHeight: '95%'
          }}>
            <img 
              src={viewer} 
              style={{
                maxWidth: '100%', 
                maxHeight: '100%',
                borderRadius: '10px',
                boxShadow: '0 20px 60px rgba(0,0,0,0.5)'
              }} 
            />
            <button
              onClick={() => setViewer(null)}
              style={{
                position: 'absolute',
                top: '10px',
                right: '10px',
                background: 'rgba(255,255,255,0.9)',
                border: 'none',
                borderRadius: '50%',
                width: '40px',
                height: '40px',
                fontSize: '1.2rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
    </>
  )
}
