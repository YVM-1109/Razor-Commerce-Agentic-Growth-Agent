import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { ArrowRight, Bot, Check, Cpu, Gauge, Monitor, Package, ShieldCheck, ShoppingBag, Sparkles, X, Zap } from 'lucide-react';
import './App.css';

const API=import.meta.env.VITE_API_URL||'http://localhost:8000/api';
const api=axios.create({baseURL:API});
const money=(n:number)=>`₹${Number(n||0).toLocaleString('en-IN',{maximumFractionDigits:0})}`;

type Product={id:string;name:string;slug:string;brand:string;description:string;price:number;category_id:string;specifications:any;pc_attributes:any;available:number};
type Cart={id:string;customer_session_id:string;status:string;subtotal:number;discount_total:number;total:number;items:any[]};

function useSession(){
 const [sessionId,setSessionId]=useState<string|null>(null);
 useEffect(()=>{
  let active=true;
  const bootstrap=async()=>{
   const stored=localStorage.getItem('ac_session');
   if(stored){
    try{
     await api.get(`/sessions/${stored}`);
     if(active){setSessionId(stored);return;}
    }catch{
     localStorage.removeItem('ac_session');
    }
   }
   try{
    const r=await api.post('/sessions',{});
    if(!active)return;
    localStorage.setItem('ac_session',r.data.id);
    setSessionId(r.data.id);
   }catch{
    if(active)setSessionId(null);
   }
  };
  bootstrap();
  return()=>{active=false};
 },[]);
 return sessionId;
}

function Header({cartCount,onCart}:{cartCount:number;onCart:()=>void}){
 return <header className="topbar"><Link className="brand" to="/"><span className="brand-mark"><Zap size={17}/></span>Razor<span>Commerce</span></Link><nav><Link to="/">Store</Link><a href="#agent">AI Agent</a><Link to="/builder">PC Builder</Link><Link to="/admin">Merchant</Link></nav><button className="cart-pill" onClick={onCart}><ShoppingBag size={18}/><span>Cart</span>{cartCount>0&&<b>{cartCount}</b>}</button></header>
}

function ProductCard({p,onAdd}:{p:Product;onAdd:(id:string)=>void}){
 return <article className="product-card">
   <div className="product-visual"><div className="visual-grid"></div><span>{p.brand}</span><Package size={58}/></div>
   <div className="product-meta"><span className="eyebrow">{p.specifications?.segment==='demo'?'BUILDATHON PICK':'CATALOGUE'}</span><h3>{p.name}</h3><p>{p.description}</p><div className="price-row"><strong>{money(p.price)}</strong><span className={p.available>0?'stock':'stock out'}>{p.available>0?`${p.available} in stock`:'Out of stock'}</span></div><button className="primary small" disabled={!p.available} onClick={()=>onAdd(p.id)}>{p.available?'Add to cart':'Unavailable'}<ArrowRight size={16}/></button></div>
 </article>
}

function CartDrawer({sessionId,onClose,onCheckout}:{sessionId:string;onClose:()=>void;onCheckout:(order:any)=>void}){
 const [cart,setCart]=useState<Cart|null>(null);const [loading,setLoading]=useState(true);const [paying,setPaying]=useState(false);const [message,setMessage]=useState('');
 const load=()=>api.get(`/cart/${sessionId}`).then(r=>setCart(r.data)).finally(()=>setLoading(false));useEffect(()=>{load()},[sessionId]);
 const change=async(id:string,q:number)=>{await api.patch(`/cart/${sessionId}/items/${id}`,{quantity:q});await load()};
 const checkout=async()=>{if(!cart||!cart.items.length)return;setPaying(true);setMessage('Creating secure payment…');try{const {data}=await api.post('/checkout/create-order',{cart_id:cart.id});
   if(data.demo_mode){await new Promise(r=>setTimeout(r,700));await api.post(`/checkout/demo-capture/${data.order_id}`);onCheckout(data);}
   else{await load();const script=document.createElement('script');script.src='https://checkout.razorpay.com/v1/checkout.js';script.onload=()=>{const rz=new (window as any).Razorpay({key:data.key_id,amount:Math.round(data.amount*100),currency:data.currency,name:'RazorCommerce',description:'Agentic Commerce demo',order_id:data.razorpay_order_id,handler:async()=>{setMessage('Payment submitted. Waiting for Razorpay server confirmation…');let confirmed=false;for(let i=0;i<10&&!confirmed;i++){await new Promise(r=>setTimeout(r,1000));const status=await api.get(`/checkout/payment-status/${data.order_id}`);confirmed=status.data.payment_status==='SUCCESS';}if(confirmed)onCheckout(data);else setMessage('Payment is pending server confirmation. Refresh the cart shortly.')},theme:{color:'#7c5cff'}});rz.open()};document.body.appendChild(script)}
 }catch(e){setMessage('Payment could not be created. Check the API status.')}finally{setPaying(false)}};
 return <div className="drawer-backdrop" onClick={onClose}><aside className="cart-drawer" onClick={e=>e.stopPropagation()}><div className="drawer-head"><div><span className="eyebrow">YOUR SESSION</span><h2>Shopping cart</h2></div><button className="icon-btn" onClick={onClose}><X/></button></div>{loading?<div className="empty">Loading cart…</div>:!cart?.items.length?<div className="empty"><ShoppingBag size={42}/><h3>Your cart is waiting</h3><p>Add a product and the Sales Agent can help you convert it into a purchase.</p></div>:<><div className="cart-lines">{cart.items.map(i=><div className="cart-line" key={i.id}><div><b>{i.product.name}</b><small>{money(i.unit_price)} each</small><div className="qty"><button onClick={()=>change(i.id,i.quantity-1)}>−</button><span>{i.quantity}</span><button onClick={()=>change(i.id,i.quantity+1)}>+</button></div></div><strong>{money(i.line_total)}</strong></div>)}</div><div className="summary"><div><span>Subtotal</span><b>{money(cart.subtotal)}</b></div>{cart.discount_total>0&&<div className="discount"><span>Agent offer</span><b>−{money(cart.discount_total)}</b></div>}<div className="total"><span>Total</span><b>{money(cart.total)}</b></div></div><button className="primary checkout" onClick={checkout} disabled={paying}>{paying?'Processing…':'Pay securely with Razorpay'}<ArrowRight/></button>{message&&<p className="helper">{message}</p>}</>}</aside></div>
}

function AgentWidget({sessionId,cart,onAddToCart}:{sessionId:string;cart:Cart|null;onAddToCart:(id:string)=>Promise<void>}){
 const [open,setOpen]=useState(false);const [text,setText]=useState('');const [messages,setMessages]=useState<any[]>([]);const [loading,setLoading]=useState(false);const [recovery,setRecovery]=useState<any>(null);const [adding,setAdding]=useState<string|null>(null);
 useEffect(()=>{if(!cart?.id)return;const t=setInterval(async()=>{try{const r=await api.post('/recovery/evaluate',null,{params:{cart_id:cart.id}});if(r.data.eligible){setRecovery(r.data);if(!open)setOpen(true)}}catch{}},5000);return()=>clearInterval(t)},[cart?.id,open]);
 const send=async()=>{if(!text.trim()||loading)return;const m=text.trim();setText('');setMessages(x=>[...x,{role:'user',text:m}]);setLoading(true);try{const r=await api.post('/chat',{session_id:sessionId,cart_id:cart?.id,message:m});setMessages(x=>[...x,{role:'agent',text:r.data.response,suggestions:r.data.product_suggestions,handoff:r.data.handoff_to_pc_builder}]);if(r.data.recovery_session_id)setRecovery({recovery_session_id:r.data.recovery_session_id})}catch{setMessages(x=>[...x,{role:'agent',text:'I’m temporarily unavailable. Please try again in a moment.'}])}finally{setLoading(false)}};
 const addSuggestion=async(id:string)=>{setAdding(id);try{await onAddToCart(id)}finally{setAdding(null)}};
 return <><button className="agent-fab" onClick={()=>setOpen(true)}><Bot size={22}/><span>AI Sales Agent</span>{recovery&&<i/>}</button>{open&&<div className="agent-panel" id="agent"><div className="agent-head"><div className="agent-avatar"><Sparkles size={18}/></div><div><b>AI Sales Agent</b><small>Grounded in catalogue & inventory</small></div><button className="icon-btn" onClick={()=>setOpen(false)}><X/></button></div><div className="agent-body">{messages.length===0&&<div className="welcome"><span>Hi — I’m here to help you finish the right purchase.</span><div className="quick"><button onClick={()=>setText('Can you find a better value option?')}>Better value</button><button onClick={()=>setText('Is this in stock?')}>Check stock</button><button onClick={()=>setText('Build my PC')}>Build my PC</button></div></div>}{messages.map((m,i)=><div key={i} className={`bubble ${m.role}`}><span>{m.text}</span>{m.suggestions?.length>0&&<div className="suggestions">{m.suggestions.map((p:any)=><div key={p.id}><div><b>{p.name}</b><span>{money(p.price)}</span></div><button className="secondary small" disabled={adding===p.id} onClick={()=>addSuggestion(p.id)}>{adding===p.id?'Adding…':'Add'}</button></div>)}</div>}{m.handoff&&<Link className="secondary small" to="/builder" onClick={()=>setOpen(false)}>Open PC Builder <ArrowRight size={14}/></Link>}</div>)}{loading&&<div className="bubble agent">Thinking…</div>}</div><div className="agent-compose"><input value={text} onChange={e=>setText(e.target.value)} onKeyDown={e=>e.key==='Enter'&&send()} placeholder="Ask about a product, price, or PC build…"/><button onClick={send}><ArrowRight size={18}/></button></div></div>}</>
}

function Storefront(){
 const sessionId=useSession();const [products,setProducts]=useState<Product[]>([]);const [categories,setCategories]=useState<any[]>([]);const [filter,setFilter]=useState('');const [cart,setCart]=useState<Cart|null>(null);const [drawer,setDrawer]=useState(false);const [notice,setNotice]=useState('');const [order,setOrder]=useState<any>(null);
 const load=()=>sessionId&&api.get(`/cart/${sessionId}`).then(r=>setCart(r.data));useEffect(()=>{Promise.all([api.get('/products'),api.get('/products/categories')]).then(([p,c])=>{setProducts(p.data);setCategories(c.data)});},[]);useEffect(()=>{load()},[sessionId]);
 const add=async(id:string)=>{
  if(!sessionId)return;
  try{
   await api.post(`/cart/${sessionId}/items`,{product_id:id,quantity:1});
   await load();
   setNotice('Added to your cart');
   setTimeout(()=>setNotice(''),1800);
  }catch(e:any){
   const detail=e?.response?.data?.detail;
   setNotice(detail==='PRODUCT_OUT_OF_STOCK'?'Product is out of stock':detail==='SESSION_NOT_FOUND'?'Session expired. Refreshing…':'Could not add the product to cart');
   if(detail==='SESSION_NOT_FOUND'){
    localStorage.removeItem('ac_session');
    window.location.reload();
   }else{
    setTimeout(()=>setNotice(''),2200);
   }
  }
 };
 const visible=useMemo(()=>filter?products.filter(p=>p.category_id===filter):products,[products,filter]);
 return <div><Header cartCount={cart?.items.reduce((a,i)=>a+i.quantity,0)||0} onCart={()=>setDrawer(true)}/><main className="store-page"><section className="hero"><div className="hero-copy"><span className="eyebrow live"><i/> AGENTIC COMMERCE DEMO</span><h1>Turn shopping intent into <em>revenue.</em></h1><p>RazorCommerce combines real-time catalogue intelligence, cart recovery, conversational selling and a constraint-aware PC Builder in one merchant-ready flow.</p><div className="hero-actions"><button className="primary" onClick={()=>document.getElementById('catalogue')?.scrollIntoView({behavior:'smooth'})}>Explore catalogue <ArrowRight/></button><Link className="secondary" to="/builder">Build a PC <Cpu/></Link></div><div className="hero-trust"><span><ShieldCheck/> Server-authoritative pricing</span><span><Zap/> Razorpay Test Mode</span><span><Gauge/> Live inventory</span></div></div><div className="hero-art"><div className="orb orb1"></div><div className="orb orb2"></div><div className="agent-card"><div className="agent-card-top"><span className="status-dot"></span> Agent online <span>NOW</span></div><div className="agent-card-title">“I found a compatible build<br/>under your budget.”</div><div className="mini-build"><div><Cpu/><span>CPU</span><b>Ryzen 5</b></div><div><Monitor/><span>GPU</span><b>RTX 4070</b></div><div><Package/><span>READY</span><b>₹1.42L</b></div></div></div></div></section>
 <section className="proof-strip"><div><b>11</b><span>catalogue categories</span></div><div><b>3</b><span>merchant controls</span></div><div><b>1</b><span>discount per recovery</span></div><div><b>3h</b><span>recovery attribution</span></div></section>
 <section id="catalogue" className="catalogue"><div className="section-head"><div><span className="eyebrow">LIVE CATALOGUE</span><h2>Shop the hardware stack</h2></div><div className="filters"><button className={!filter?'active':''} onClick={()=>setFilter('')}>All</button>{categories.map(c=><button key={c.id} className={filter===c.id?'active':''} onClick={()=>setFilter(c.id)}>{c.name}</button>)}</div></div><div className="product-grid">{visible.map(p=><ProductCard p={p} onAdd={add} key={p.id}/>)}</div></section>
 <section className="builder-banner"><div><span className="eyebrow">FIRST-CLASS AI CAPABILITY</span><h2>Build a PC without guessing.</h2><p>Hard budget. Compatibility validation. Inventory checks. Explicit approval before anything touches your cart.</p></div><Link className="primary" to="/builder">Open PC Builder <ArrowRight/></Link></section></main>{sessionId&&<AgentWidget sessionId={sessionId} cart={cart} onAddToCart={add}/>} {drawer&&sessionId&&<CartDrawer sessionId={sessionId} onClose={()=>setDrawer(false)} onCheckout={o=>setOrder(o)}/>} {notice&&<div className="toast">{notice}<Check size={16}/></div>}{order&&<div className="success-overlay"><div className="success-card"><div className="success-icon"><Check/></div><span className="eyebrow">PAYMENT VERIFIED</span><h2>Purchase recovered.</h2><p>Your demo payment was captured and the server calculated attribution from the latest meaningful agent interaction.</p><div className="success-meta"><span>Order</span><b>{order.order_id?.slice(0,8)}…</b></div><button className="primary" onClick={()=>{setOrder(null);setDrawer(false);load()}}>Continue shopping <ArrowRight/></button></div></div>}</div>
}

function parseBudget(text:string){
 const m=text.match(/(?:under|below|less than|upto|up to|budget(?:\s+of)?|within)\s*[₹$]?\s*([\d,]+)/i) || text.match(/[₹$]\s*([\d,]+)/i);
 return m ? Number(m[1].replace(/,/g,'')) : 100000;
}

function Builder(){
 const sessionId=useSession();const [builder,setBuilder]=useState<any>(null);const [prompt,setPrompt]=useState('');const [busy,setBusy]=useState(false);const [message,setMessage]=useState('');
 const start=async()=>{if(!sessionId||!prompt.trim()){setMessage('Tell the builder what you want and include a hard budget.');return;}setBusy(true);try{let s=builder;if(!s){const r=await api.post('/pc-builder/sessions',null,{params:{session_id:sessionId}});s=r.data;setBuilder(s)}const budget=parseBudget(prompt);await api.post(`/pc-builder/sessions/${s.id}/requirements`,{budget,use_case:'gaming',resolution:'1440p',include_peripherals:false,prompt:prompt});const r=await api.post(`/pc-builder/sessions/${s.id}/generate`);setBuilder(r.data);setMessage(r.data.status==='PROPOSED'?`Validated build under ${money(r.data.budget)}. Review every component before approval.`:(r.data.message||'No valid build exists within that budget.'));}catch(e:any){setMessage(e?.response?.data?.detail||'Could not generate the build. Check the API status.')}finally{setBusy(false)}};
 const approve=async()=>{if(!builder)return;setBusy(true);try{await api.post(`/pc-builder/sessions/${builder.id}/approve`,{version_number:builder.version});const c=await api.post(`/pc-builder/sessions/${builder.id}/commit`);setBuilder(c.data.build);setMessage(`Approved and added to cart ${c.data.cart_id.slice(0,8)}…`)}catch(e:any){setMessage(e?.response?.data?.detail||'The build changed or is no longer valid. Generate again.')}finally{setBusy(false)}};
 const validation=builder?.validation||{};
 return <div><Header cartCount={0} onCart={()=>{}}/><main className="builder-page"><div className="builder-intro"><Link to="/" className="back">← Back to store</Link><span className="eyebrow">PC BUILDER AGENT</span><h1>Design a compatible PC<br/><em>within a hard budget.</em></h1><p>The agent proposes components, validates compatibility and stock deterministically, and waits for your explicit approval before cart mutation.</p></div><div className="builder-layout"><section className="builder-form card"><span className="step">01 / REQUIREMENTS</span><h2>Tell us what you need</h2><label>Prompt<input value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder="e.g. Build me a gaming PC under ₹100000"/></label><button className="primary full" onClick={start} disabled={busy}>{busy?'Building…':'Generate compatible build'}<Sparkles/></button>{message&&<div className="builder-message">{message}</div>}</section>{builder?.components?.length?<section className="build-proposal card"><div className="proposal-head"><div><span className="step">02 / PROPOSAL</span><h2>Validated configuration</h2></div><span className={validation.budget&&validation.compatibility&&validation.inventory?'valid':'invalid'}>{validation.budget&&validation.compatibility&&validation.inventory?<><Check size={15}/> All checks passed</>:<>Validation failed</>}</span></div><div className="validation"><span>{validation.budget?<Check/>:<X/>} Budget</span><span>{validation.compatibility?<Check/>:<X/>} Compatibility</span><span>{validation.inventory?<Check/>:<X/>} Inventory</span></div><div className="build-list">{builder.components.map((c:any)=><div className="build-row" key={c.id+c.role}><span className="role">{c.role}</span><div><b>{c.name}</b><small>{c.available} available</small></div><strong>{money(c.price)}</strong></div>)}</div><div className="build-total"><span>Total</span><b>{money(builder.total)}</b><small>Hard budget {money(builder.budget)}</small></div>{builder.approved?<div className="approved"><Check/> Build approved and committed to cart.</div>:validation.budget&&validation.compatibility&&validation.inventory?<button className="primary full" onClick={approve} disabled={busy}>{busy?'Validating…':'Approve build & add to cart'}<ArrowRight/></button>:<button className="secondary full" onClick={start} disabled={busy}>Rebuild within constraints <Sparkles/></button>}<p className="fine">Approval is bound to build version {builder.version}. Any replacement requires a new validated version and approval.</p></section>:<section className="build-empty card"><div className="empty-visual"><Cpu size={48}/></div><span className="eyebrow">WAITING FOR REQUIREMENTS</span><h2>Your build will appear here</h2><p>We will validate the hard budget, component compatibility and live inventory before asking you to approve anything.</p></section>}</div></main></div>
}

function Admin(){
 const [token,setToken]=useState(localStorage.getItem('merchant_token'));const [email,setEmail]=useState('demo@merchant.com');const [password,setPassword]=useState('demo123');const [data,setData]=useState<any>(null);const [config,setConfig]=useState<any>(null);const [tab,setTab]=useState('overview');const [saving,setSaving]=useState(false);
 const load=async(t=token)=>{if(!t)return;const [d,c]=await Promise.all([api.get('/merchant/dashboard',{headers:{Authorization:`Bearer ${t}`}}),api.get('/merchant/config',{headers:{Authorization:`Bearer ${t}`}})]);setData(d.data);setConfig(c.data)};useEffect(()=>{load()},[token]);
 const login=async()=>{const r=await api.post('/merchant/auth/login',{email,password});localStorage.setItem('merchant_token',r.data.access_token);setToken(r.data.access_token)};const save=async()=>{setSaving(true);await api.patch('/merchant/config',config,{headers:{Authorization:`Bearer ${token}`}});await load();setSaving(false)};
 if(!token)return <div className="login-page"><div className="login-card card"><span className="eyebrow">MERCHANT PORTAL</span><h1>Welcome back.</h1><p>Use the demo merchant credentials to open the growth command center.</p><input value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email"/><input value={password} onChange={e=>setPassword(e.target.value)} type="password" placeholder="Password"/><button className="primary full" onClick={login}>Open dashboard <ArrowRight/></button><small>Demo: demo@merchant.com / demo123</small></div></div>
 const k=data?.kpis||{};return <div className="admin-page"><aside className="admin-nav"><Link className="brand" to="/"><span className="brand-mark"><Zap size={17}/></span>Razor<span>Commerce</span></Link><div className="merchant-id"><div className="merchant-avatar">DM</div><div><b>Demo Merchant</b><small>Growth workspace</small></div></div>{['overview','products','configuration'].map(t=><button className={tab===t?'active':''} key={t} onClick={()=>setTab(t)}>{t==='overview'?'Overview':t==='products'?'Product analytics':'Configuration'}</button>)}<Link to="/" className="store-link">← Back to storefront</Link></aside><main className="admin-main"><div className="admin-top"><div><span className="eyebrow live"><i/> LIVE MERCHANT VIEW</span><h1>{tab==='overview'?'Growth command center':tab==='products'?'Product performance':'Merchant controls'}</h1></div><button className="secondary" onClick={()=>load()}>Refresh data</button></div>{tab==='overview'&&<><div className="kpi-grid">{[['Total revenue',money(k.total_revenue),'revenue'],['Revenue at risk',money(k.revenue_at_risk),'risk'],['Recovered revenue',money(k.revenue_recovered),'recovered'],['Recovery rate',`${Number(k.recovery_rate||0).toFixed(1)}%`,'rate'],['Abandoned carts',k.abandoned_carts,'cart'],['Agent interventions',k.agent_interventions,'agent']].map(([a,b,c])=><div className="kpi card" key={a}><span>{a}</span><b>{b}</b><small>{c==='risk'?'Eligible cart value waiting for recovery':c==='recovered'?'Attributed to agent-assisted purchases':'Live from PostgreSQL'}</small></div>)}</div><div className="admin-grid"><section className="card table-card"><div className="table-head"><div><span className="eyebrow">RECENT ORDERS</span><h2>Commerce outcomes</h2></div></div><table><thead><tr><th>Status</th><th>Value</th><th>Attribution</th><th>Order</th></tr></thead><tbody>{data?.orders?.map((o:any)=><tr key={o.id}><td><span className={`status ${o.status.toLowerCase()}`}>{o.status}</span></td><td>{money(o.total)}</td><td><span className={`attr ${o.attribution.toLowerCase()}`}>{o.attribution}</span></td><td>#{o.id.slice(0,8)}</td></tr>)}{!data?.orders?.length&&<tr><td colSpan={4}>No orders yet — run the storefront demo.</td></tr>}</tbody></table></section><section className="card activity-card"><div className="table-head"><div><span className="eyebrow">RECOVERY PIPELINE</span><h2>Agent activity</h2></div></div>{data?.recoveries?.slice(0,6).map((r:any)=><div className="activity-row" key={r.id}><div className="activity-icon"><Bot size={17}/></div><div><b>Recovery {r.id.slice(0,8)}</b><small>{r.interventions} intervention(s) · {r.status}</small></div><span>{r.whatsapp_sent?'WhatsApp sent':'Web only'}</span></div>)}{!data?.recoveries?.length&&<div className="empty small">No recovery sessions yet.</div>}</section></div></>}{tab==='products'&&<section className="card table-card"><div className="table-head"><div><span className="eyebrow">CATALOGUE ANALYTICS</span><h2>Product recovery signals</h2></div></div><table><thead><tr><th>Product</th><th>Abandoned</th><th>Interventions</th><th>Recovered</th><th>Revenue</th></tr></thead><tbody>{data?.products?.map((p:any)=><tr key={p.product}><td><b>{p.product}</b></td><td>{p.abandoned}</td><td>{p.interventions}</td><td>{p.recovered}</td><td>{money(p.revenue_recovered)}</td></tr>)}</tbody></table></section>}{tab==='configuration'&&config&&<section className="config-card card"><span className="eyebrow">ONLY THREE CONTROLS</span><h2>Set the guardrails.</h2><p>These values are enforced by deterministic commerce services; the LLM cannot override them.</p><label>Maximum discount (%)<input type="number" value={config.maximum_discount_pct} onChange={e=>setConfig({...config,maximum_discount_pct:Number(e.target.value)})}/></label><label>Maximum interventions<input type="number" value={config.maximum_interventions} onChange={e=>setConfig({...config,maximum_interventions:Number(e.target.value)})}/></label><label>Minimum cart value (₹)<input type="number" value={config.minimum_cart_value} onChange={e=>setConfig({...config,minimum_cart_value:Number(e.target.value)})}/></label><button className="primary" onClick={save} disabled={saving}>{saving?'Saving…':'Save controls'}<Check/></button></section>}</main></div>
}

function App(){return <BrowserRouter><Routes><Route path="/" element={<Storefront/>}/><Route path="/builder" element={<Builder/>}/><Route path="/admin" element={<Admin/>}/></Routes></BrowserRouter>}
export default App;
