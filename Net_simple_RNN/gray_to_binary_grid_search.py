from __future__ import print_function
import numpy as np
import random
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter
from torch.optim.lr_scheduler import StepLR
import winsound

torch.random.manual_seed(10)

pixel_depth = 24
pixel_depth_format = '0{}b'.format(pixel_depth)

def decimal_to_gray_decimal(n):
    return n ^ (n >> 1)

def gray_to_binary(n):
    n = int(n, 2) # convert to int
    mask = n
    while mask != 0:
        mask >>= 1
        n ^= mask # n=n^mask
    return format(n, pixel_depth_format)

def get_sample(pixel_depth):
    # lower_bound = 0
    # upper_bound = pow(2, pixel_depth) - 1
    #
    # input_as_decimal = random.randint(lower_bound, upper_bound)
    numbers_set = [16777215, 437, 570790, 31096, 2890, 1896986,
                   7790, 5832087, 47082, 930973, 32, 84007, 7986310,
                   4208, 730037, 11402072]
    input_as_decimal = numbers_set[random.randint(0, 15)]
    input_as_gray_decimal = decimal_to_gray_decimal(input_as_decimal)
    input_as_gray_code = format(input_as_gray_decimal, pixel_depth_format)
    input_as_binary = gray_to_binary(input_as_gray_code)
    input_as_gray_code = np.array(list(input_as_gray_code), dtype=int) #np.array(list(input_as_gray_code[::-1]), dtype=int)
    input_as_binary = np.array(list(input_as_binary), dtype=int)

    return input_as_gray_code, input_as_binary


class Adder (nn.Module):
  def __init__(self, input_size, hidden_size, output_size, num_layers):
    super(Adder, self).__init__()
    self.rnn = nn.GRU(input_size, hidden_size, num_layers)
    self.outputLayer = nn.Linear(hidden_size, output_size)
    self.sigmoid = nn.Sigmoid()

  def forward(self, input):
    out, hidd = self.rnn(input)
    T, B, D = out.size(0), out.size(1), out.size(2)
    out = out.contiguous()
    out = out.view(B*T, D)
    outputLayer = self.outputLayer(out)
    outputLayer = outputLayer.view(T, B, -1).squeeze(1)
    output = self.sigmoid(outputLayer)
    return output, hidd

input_size = 1
output_size = 1
lossFunction = nn.MSELoss()
epochs = 20000
learn_rate = 0.1
#hidden_sizes = [8, 16, 32, 64, 96, 128, 256]
hidden_sizes = [32, 32, 32, 32, 32,
                48, 48, 48, 48, 48,
                64, 64, 64, 64, 64,
                80, 80, 80, 80, 80,
                96, 96, 96, 96, 96,
                112, 112, 112, 112, 112,
                128, 128, 128, 128, 128]
layers = [1]

for i, hidden_size in enumerate(hidden_sizes):
    for j, num_layers in enumerate(layers):
        model = Adder(input_size, hidden_size, output_size, num_layers)
        model.rnn.weight_hh_l0 = nn.Parameter(1 * torch.randn_like(model.rnn.weight_hh_l0))
        model.rnn.weight_ih_l0 = nn.Parameter(1 * torch.randn_like(model.rnn.weight_ih_l0))
        print('after init: {}'.format(model.rnn.weight_ih_l0))
        print('Model initialized')
        print('Hidden size: {}'.format(hidden_size))
        print('Layers: {}'.format(num_layers))
        optimizer = optim.SGD(model.parameters(), lr=learn_rate)
        #scheduler = StepLR(optimizer, step_size=1000, gamma=0.2)

        gradient_sum_hh = 0
        gradient_sum_ih = 0

        #writer = SummaryWriter(log_dir='runs/f_lr0_05/hidd_{:03d}_layers_{:03d}'.format(hidden_size, num_layers))
        writer = SummaryWriter(log_dir='runs/L1/idx_{:02d}_hidd_{:03d}'.format(i, hidden_size, num_layers))

        for i in range(0, epochs):
            x, y = get_sample(pixel_depth)
            optimizer.zero_grad()

            x_var = torch.from_numpy(x).unsqueeze(1).float()
            x_var = x_var.unsqueeze(1)
            x_var = x_var.contiguous()
            y_var = torch.from_numpy(y).float()

            predicted_output, hidd = model(x_var)
            predicted_output = predicted_output.squeeze(-1)
            loss = lossFunction(predicted_output, y_var)
            loss.backward()
            optimizer.step()
            #scheduler.step()

            # writer.add_hparams({'lr': learn_rate, 'bsize': 1},
            #                    {'hidden_size': hidden_size, 'layers': num_layers})

            writer.add_scalar("Loss/train", loss, i)

            writer.add_scalar("Weight_ih/[4][0]", model.rnn.weight_ih_l0[4][0].item(), i)
            writer.add_scalar("Weight_ih/[17][0]", model.rnn.weight_ih_l0[17][0].item(), i)
            writer.add_scalar("Weight_ih/[3][0]", model.rnn.weight_ih_l0[3][0].item(), i)
            writer.add_scalar("Weight_ih/[25][0]", model.rnn.weight_ih_l0[25][0].item(), i)

            writer.add_scalar("Weight_grad_ih/[4][0]", model.rnn.weight_ih_l0.grad[4][0].item(), i)
            writer.add_scalar("Weight_grad_ih/[17][0]", model.rnn.weight_ih_l0.grad[17][0].item(), i)
            writer.add_scalar("Weight_grad_ih/[3][0]", model.rnn.weight_ih_l0.grad[3][0].item(), i)
            writer.add_scalar("Weight_grad_ih/[25][0]", model.rnn.weight_ih_l0.grad[25][0].item(), i)

            writer.add_scalar("Weight_hh/[4][3]", model.rnn.weight_hh_l0[4][3].item(), i)
            writer.add_scalar("Weight_hh/[23][2]", model.rnn.weight_hh_l0[23][2].item(), i)
            writer.add_scalar("Weight_hh/[3][25]", model.rnn.weight_hh_l0[3][25].item(), i)
            writer.add_scalar("Weight_hh/[4][2]", model.rnn.weight_hh_l0[4][2].item(), i)

            writer.add_scalar("Weight_grad_hh/[4][3]", model.rnn.weight_hh_l0.grad[4][3].item(), i)
            writer.add_scalar("Weight_grad_hh/[23][2]", model.rnn.weight_hh_l0.grad[23][2].item(), i)
            writer.add_scalar("Weight_grad_hh/[3][25]", model.rnn.weight_hh_l0.grad[3][25].item(), i)
            writer.add_scalar("Weight_grad_hh/[4][2]", model.rnn.weight_hh_l0.grad[4][2].item(), i)

            for row in range(hidden_size):
                for col in range(hidden_size):
                    gradient_sum_hh = gradient_sum_hh + model.rnn.weight_hh_l0.grad[row][col]

            for row in range(hidden_size):
                for col in range(input_size):
                    gradient_sum_ih = gradient_sum_ih + model.rnn.weight_ih_l0.grad[row][col]

            if not i%1000:
                print('epoch {}, loss:{:.4f}'
                      .format(i, loss.item()))#, scheduler.get_lr()[0]))  ; lr:{:.9f}
            writer.add_scalar("Grad_SUM/hh", gradient_sum_hh, i)
            writer.add_scalar("Grad_SUM/ih", gradient_sum_ih, i)

        writer.flush()
        writer.close()



###### Testing the model ######

for i in range(0, 5):
    x, y = get_sample(pixel_depth)
    print('----------------------------------------- test {} ---'.format(i))
    print('gray code: {}'.format(x))
    print('gray as binary equals: {}'.format(y))
    x_var = torch.from_numpy(x).unsqueeze(1).float()
    x_var = x_var.unsqueeze(1)
    x_var = x_var.contiguous()
    y_var = torch.from_numpy(y).float()
    predicted_output, hidd = model(x_var)
    predicted_output = predicted_output.squeeze(-1)
    predicted_output = predicted_output.detach().numpy()
    bits = np.round(predicted_output)
    bits = bits.astype(int)
    result = all(bits == y)
    print('model output is {}'.format(bits))
    print('predication equals result: {}'.format(result))

duration = 1000  # milliseconds
freq = 440  # Hz
winsound.Beep(freq, duration)


