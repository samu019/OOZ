const TronWeb = require('tronweb');

const tronWeb = new TronWeb({
  fullHost: 'https://api.trongrid.io',
  privateKey: 'TU_CLAVE_PRIVADA'  // Aquí va tu clave privada para realizar transacciones
});

async function sendUSDT(fromAddress, toAddress, amount) {
  const contract = await tronWeb.contract().at('TALA6z6EtKX9EzFVYwWPTjPLGZ9pQxiRE6');  // Dirección del contrato de USDT (TRC20)
  
  const decimals = await contract.decimals().call();  // Obtener los decimales del contrato
  const amountToSend = tronWeb.toSun(amount * Math.pow(10, decimals));  // Convertir monto a unidades base (sun)
  
  try {
      const result = await contract.transfer(toAddress, amountToSend).send({
        from: fromAddress,
        feeLimit: 100000000
      });
      console.log("Transferencia exitosa:", result);
  } catch (error) {
      console.error("Error al enviar USDT:", error);
  }
}

const fromAddress = process.argv[2];  // Dirección interna de la billetera
const toAddress = process.argv[3];    // Dirección de retiro (TRC20)
const amount = parseFloat(process.argv[4]);  // Monto a enviar

sendUSDT(fromAddress, toAddress, amount);
