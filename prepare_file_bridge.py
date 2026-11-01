#!/usr/bin/env python3
"""Prepare an isolated My-files bridge on the already reviewed browser source."""
import argparse
import hashlib
from pathlib import Path

EXPECTED={
 'apps/vectorcraft-web/src/api.rs':'f9232385c01d7b2dcd878a941940bac578e4def69b3949c017645b40618f8bad',
 'apps/vectorcraft-web/src/web.rs':'469768a0fef4f9314808a58a9b4608d7d89576d42ff821c0b69e6a2a96c912cd',
 'crates/ui-egui/src/embroidery/viewer.rs':'22d7ab44e9fc4de254a6046f1b6628780de773632914ad93bdde26f4f1c878a4',
}
def replace(text,old,new,count=1):
 if text.count(old)!=count:raise ValueError('Unexpected source pattern: '+old[:100])
 return text.replace(old,new)
def prepare(source):
 source=Path(source).resolve();paths={k:source/k for k in EXPECTED};files={}
 for name,path in paths.items():
  raw=path.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=EXPECTED[name]:raise ValueError('Unexpected source: '+name)
  files[name]=raw.decode()
 name='apps/vectorcraft-web/src/api.rs';t=files[name]
 t=replace(t,'use vectorcraft_ui_egui::ControlRequest;','use vectorcraft_ui_egui::ControlRequest;\nuse vectorcraft_ui_egui::place::{PlaceArrival, PlaceInbox};')
 t=replace(t,'    static INBOX: RefCell<Option<Inbox>> = const { RefCell::new(None) };','    static INBOX: RefCell<Option<Inbox>> = const { RefCell::new(None) };\n    static PLACE_INBOX: RefCell<Option<PlaceInbox>> = const { RefCell::new(None) };')
 t=replace(t,'pub fn connect(tx: Option<Sender<ControlRequest>>, inbox: Inbox, ctx: egui::Context) {','pub fn connect(tx: Option<Sender<ControlRequest>>, inbox: Inbox, place_inbox: PlaceInbox, ctx: egui::Context) {')
 t=replace(t,'    INBOX.with(|i| *i.borrow_mut() = Some(inbox));','    INBOX.with(|i| *i.borrow_mut() = Some(inbox));\n    PLACE_INBOX.with(|i| *i.borrow_mut() = Some(place_inbox));')
 marker='    set_fn(&obj, "captureDownloads", Closure::<dyn Fn(bool)>::new(|on: bool| CAPTURE.with(|c| c.set(on))).into_js_value())?;'
 insert='''    set_fn(
        &obj,
        "placeFile",
        Closure::<dyn Fn(String, js_sys::Uint8Array) -> JsValue>::new(|name: String, bytes: js_sys::Uint8Array| {
            if bytes.length() > 128 * 1024 * 1024 || name.is_empty() || name.contains(['/', '\\\\']) {
                return JsValue::FALSE;
            }
            let queued = PLACE_INBOX.with(|i| {
                i.borrow().as_ref().is_some_and(|inbox| {
                    inbox.lock().unwrap_or_else(|e| e.into_inner()).push(PlaceArrival { name, bytes: bytes.to_vec(), drop: None });
                    true
                })
            });
            repaint();
            JsValue::from_bool(queued)
        }).into_js_value(),
    )?;
'''
 t=replace(t,marker,insert+marker);files[name]=t
 name='apps/vectorcraft-web/src/web.rs';t=files[name]
 t=replace(t,'crate::api::connect(None, host.inbox.clone(), ctx.clone());','crate::api::connect(None, host.inbox.clone(), host.place_inbox.clone(), ctx.clone());')
 t=replace(t,'crate::api::connect(Some(control_tx), host.inbox.clone(), ctx.clone());','crate::api::connect(Some(control_tx), host.inbox.clone(), host.place_inbox.clone(), ctx.clone());')
 start=t.index('    let open_inbox = inbox.clone();',t.index('fn services('));end=t.index('        // Sample Color from Screen:',start)
 t=t[:start]+'''    let screen_color = eye_dropper(ctx.clone());
    Services {
        // The desktop handles these requests with its account-backed file picker.
        place_async: Some(Box::new(|| request_desktop_file("codi-place-my-files"))),
        place_inbox: Some(place_inbox),
        open_async: Some(Box::new(|| request_desktop_file("codi-open-my-files"))),
'''+t[end:]
 marker='/// Sample Color from Screen in the browser:'
 helper='''fn request_desktop_file(name: &str) {
    if let (Some(window), Ok(event)) = (web_sys::window(), web_sys::Event::new(name)) {
        let _ = window.dispatch_event(&event);
    }
}

'''
 t=replace(t,marker,helper+marker);files[name]=t
 name='crates/ui-egui/src/embroidery/viewer.rs';t=files[name]
 t=replace(t,'            if crate::widgets::primary_button(ui, tl!("Get StitchFoundry Free")).clicked() {','            #[cfg(not(target_arch = "wasm32"))]\n            if crate::widgets::primary_button(ui, tl!("Get StitchFoundry Free")).clicked() {');files[name]=t
 for name,t in files.items():paths[name].write_text(t)
 print('Prepared browser My-files bridge and removed external viewer promotion')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args();prepare(a.source)
