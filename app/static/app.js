"use strict";
const byId = id => document.getElementById(id);
let items = [], records = [], busy = false;
const icons = {STUDY:"⌘", PLAY:"▧", TALK:"◌"};
function element(tag, text, className) { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (className) node.className = className; return node; }
function notice(text, error=false) { const node=byId("notice");node.textContent=text;node.className=error?"error":"";node.hidden=false; }
async function request(path, data) { const response=await fetch(path,{method:data===undefined?"GET":"POST",headers:{"Content-Type":"application/json"},body:data===undefined?undefined:JSON.stringify(data)});const result=await response.json();if(!response.ok)throw new Error(typeof result.detail==="string"?result.detail:"모임과 닉네임을 확인해 주세요.");return result; }
function render() {
  byId("event-count").textContent=items.length;
  byId("joined-count").textContent=items.reduce((sum,item)=>sum+item.occupied,0);
  byId("remaining-count").textContent=items.reduce((sum,item)=>sum+item.remaining,0);
  const shelf=byId("events");shelf.replaceChildren();const picker=byId("event-choice"),old=picker.value;picker.replaceChildren(new Option("모임을 선택하세요",""));
  items.forEach(item=>{
    const card=element("article",undefined,"event"),top=element("div",undefined,"top");top.append(element("span",icons[item.category]||"✳","icon"),element("span",item.category,"tag"));
    const places=element("div",undefined,"places");places.append(element("span",`${item.occupied}/${item.capacity}명 신청`),element("strong",item.remaining?`${item.remaining}자리 남았어요`:"신청 마감"));
    const progress=element("div",undefined,"progress"),bar=element("span");bar.style.width=`${100*item.occupied/item.capacity}%`;progress.append(bar);
    const button=element("button",item.remaining?"이 모임 선택하기 ↗":"정원이 마감됐어요","pick");button.type="button";button.disabled=busy||!item.remaining;button.addEventListener("click",()=>{picker.value=String(item.id);byId("nickname").focus();});
    card.append(top,element("h3",item.title),element("p",item.description,"description"),places,progress,button);shelf.append(card);
    if(item.remaining)picker.append(new Option(item.title,String(item.id)));
  });if([...picker.options].some(option=>option.value===old))picker.value=old;
  const list=byId("records");list.replaceChildren();if(!records.length)list.append(element("p","첫 번째 신청을 기다리고 있어요.","empty"));
  records.forEach(record=>{
    const row=element("div",undefined,"record"),info=element("div"),actions=element("div",undefined,"actions");
    info.append(element("strong",record.nickname),element("p",record.title),element("p",new Date(record.created_at).toLocaleString("ko-KR",{month:"numeric",day:"numeric",hour:"2-digit",minute:"2-digit"}),"meta"));
    actions.append(element("span",record.cancelled?"취소 완료":"신청 완료",record.cancelled?"status cancelled":"status"));
    if(!record.cancelled){const cancel=element("button","신청 취소","cancel");cancel.type="button";cancel.disabled=busy;cancel.setAttribute("aria-label",`${record.nickname} 신청 취소`);cancel.addEventListener("click",()=>perform(async()=>{await request(`/api/registrations/${record.id}/cancel`,{receipt:record.receipt});notice("신청을 취소했어요. 남은 자리가 다시 열렸어요.");}));actions.append(cancel);}row.append(info,actions);list.append(row);
  });byId("refresh").disabled=busy;byId("join-form").querySelector("button").disabled=busy;
}
async function refresh(){[items,records]=await Promise.all([request("/api/events"),request("/api/registrations")]);render();}
async function perform(action){if(busy)return;busy=true;render();try{await action();await refresh();}catch(error){notice(error.message||"서버에 연결하지 못했어요.",true);}finally{busy=false;render();}}
byId("join-form").addEventListener("submit",event=>{event.preventDefault();const event_id=Number(byId("event-choice").value),nickname=byId("nickname").value.trim();perform(async()=>{await request("/api/registrations",{event_id,nickname});byId("nickname").value="";notice("신청 완료! 함께할 시간을 기다려요.");});});
byId("refresh").addEventListener("click",()=>perform(async()=>{}));
refresh().catch(error=>notice(error.message||"서버에 연결하지 못했어요.",true));
