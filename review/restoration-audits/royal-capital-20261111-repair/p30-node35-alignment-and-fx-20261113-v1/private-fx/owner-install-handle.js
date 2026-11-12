(async function installP30FxObserverWithHandle(frame,factorySource,options){
  'use strict';
  options=options||{};
  const slot=options.slot||'__stellaP30FxFirstPaintObserverV2';
  const describe=error=>{
    try{return {name:String(error?.name||'Error'),message:String(error?.message||error)};}
    catch{return {name:'Error',message:'Error details could not be read'};}
  };
  let retained=null,receipt=null;
  const fail=(message,details)=>{
    const failure=new Error(message);
    // Do not dispose the only exact owner reference when the later receipt
    // read/validation fails. The driver finally owns cleanup and disposal.
    failure.observerHandle=retained;
    failure.observerInstallationReceipt=details;
    return failure;
  };
  try{
    retained=await frame.evaluateHandle(async ({source,settings,slot})=>{
      let ownedHandle=null,ownedProof=null,ownedUninstall=null,validationCleanup=null;
      const describe=error=>{
        try{return {name:String(error?.name||'Error'),message:String(error?.message||error)};}
        catch{return {name:'Error',message:'Error details could not be read'};}
      };
      try{
        const factory=(0,eval)(source);
        if(typeof factory!=='function')throw Error('Reviewed source did not evaluate to a factory');
        const installed=await factory({...settings,slot});
        const candidate=Object.getOwnPropertyDescriptor(globalThis,slot)?.value;
        const owns=Boolean(installed?.ownerProof&&candidate?.ownerProof===installed.ownerProof);
        if(owns&&typeof candidate?.uninstall==='function'){
          ownedHandle=candidate;ownedProof=installed.ownerProof;ownedUninstall=candidate.uninstall;
        }
        if(installed?.status!=='installed_observer_only'||installed.slot!==slot||
           installed.methodCount!==6||!owns||typeof candidate?.snapshot!=='function'||
           typeof candidate?.uninstall!=='function')throw Error('Observer installation/owned-slot verification failed');
        // Verification and retention are one iframe operation. In particular,
        // proof comes from this factory result, never from a later slot lookup.
        // The host receives a JSHandle to THIS object, not a serialized clone.
        return {handle:ownedHandle,proof:ownedProof,uninstall:ownedUninstall,receipt:{
          status:'observer_install_verified',factoryStatus:installed.status,slot,
          ownedSlotVerified:true,methodCount:installed.methodCount,rootReviewed:false,rootConfirmed:false,
          exactTextBeganAvailable:installed.exactTextBeganAvailable,
          exactGlSubmissionTimestampAvailable:installed.exactGlSubmissionTimestampAvailable}};
      }catch(error){
        let cleanup=error?.observerCleanup||null;
        // Only a handle proven against this factory's proof may be touched.
        // A factory rejection can already supply its own partial rollback.
        if(ownedHandle){
          try{validationCleanup=Reflect.apply(ownedUninstall,ownedHandle,['owner-install-verification-failed']);
            cleanup=validationCleanup.cleanup;}
          catch(cleanupError){cleanup={allRestored:false,conflicts:['owner cleanup threw: '+describe(cleanupError).message]};}
        }
        return {handle:ownedHandle,proof:ownedProof,uninstall:ownedUninstall,receipt:{
          status:'observer_install_failed',slot,error:describe(error),
          originalInstallError:error?.observerInstallError||null,cleanup,validationCleanup,
          requiresFrameClosure:!cleanup?.allRestored,rootReviewed:false,rootConfirmed:false}};
      }
    },{source:factorySource,settings:options,slot});
  }catch(error){
    throw fail('Observer iframe install call failed: '+describe(error).message,
      {status:'observer_install_transport_failed',slot,error:describe(error),requiresFrameClosure:true});
  }
  try{
    // This read obtains plain metadata from the retained object. It never
    // looks up the window slot again or chooses another observer object.
    receipt=await retained.evaluate(owned=>owned.receipt);
  }catch(error){
    throw fail('Observer receipt read failed: '+describe(error).message,
      {status:'observer_install_receipt_unavailable',slot,error:describe(error),requiresFrameClosure:true});
  }
  if(receipt?.status!=='observer_install_verified'||receipt.slot!==slot||
     receipt.ownedSlotVerified!==true||receipt.methodCount!==6)
    throw fail('FX observer was not verified; do not advance the route.',receipt||
      {status:'observer_install_receipt_missing',slot,requiresFrameClosure:true});
  return {receipt,observerHandle:retained};
})
